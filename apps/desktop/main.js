const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs');
const net = require('net');
const path = require('path');

let apiProcess = null;
let mainWindow = null;
let apiPort = null;

function delay(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

async function isPortAvailable(port) {
	return await new Promise((resolve) => {
		const server = net.createServer();
		server.once('error', () => {
			resolve(false);
		});
		server.once('listening', () => {
			server.close(() => resolve(true));
		});
		server.listen(port, '127.0.0.1');
	});
}

async function pickPort(start = 9761, end = 9790) {
	for (let port = start; port <= end; port += 1) {
		if (await isPortAvailable(port)) return port;
	}
	return 0;
}

async function waitForHealthz(port, timeoutMs = 20000) {
	const deadline = Date.now() + timeoutMs;
	while (Date.now() < deadline) {
		try {
			const res = await fetch(`http://127.0.0.1:${port}/healthz`, { method: 'GET' });
			if (res.ok) return true;
		} catch {
			// ignore
		}
		await delay(250);
	}
	return false;
}

function resolveApiCommand() {
	const envPath = process.env.WRITER_AGENT_API_PATH;
	if (envPath && fs.existsSync(envPath)) {
		return { command: envPath, args: [], cwd: app.getPath('userData') };
	}

	const packagedBinary = path.join(
		process.resourcesPath,
		'api',
		process.platform === 'win32' ? 'writer-agent-api.exe' : 'writer-agent-api',
	);
	if (fs.existsSync(packagedBinary)) {
		return { command: packagedBinary, args: [], cwd: app.getPath('userData') };
	}

	const python = process.env.WRITER_AGENT_PYTHON || 'python';
	return { command: python, args: ['-m', 'app.desktop_server'], cwd: path.join(__dirname, '..', 'api') };
}

function buildDatabaseUrl(userDataDir) {
	const dbPath = path.join(userDataDir, 'writer_agent2.sqlite3');
	const normalized = dbPath.replace(/\\/g, '/');
	return `sqlite+aiosqlite:///${normalized}`;
}

async function startApi(port) {
	const commandInfo = resolveApiCommand();
	const userDataDir = app.getPath('userData');
	const staticDirFromEnv = process.env.WRITER_AGENT_STATIC_DIR || '';
	const packagedStaticDir = path.join(process.resourcesPath, 'web');
	const devStaticDir = path.join(__dirname, '..', 'web', 'build');
	const staticDir =
		staticDirFromEnv || (app.isPackaged ? packagedStaticDir : devStaticDir);

	if (app.isPackaged && !fs.existsSync(staticDir)) {
		dialog.showErrorBox('静态资源缺失', `未找到前端构建产物：${staticDir}`);
		app.quit();
		return;
	}

	const env = {
		...process.env,
		HOST: '127.0.0.1',
		PORT: String(port),
		DATABASE_URL: buildDatabaseUrl(userDataDir),
		AUTO_MIGRATE: '1',
		LICENSE_REQUIRED: process.env.WRITER_AGENT_LICENSE_REQUIRED || '1',
		LICENSE_PUBLIC_KEY: process.env.WRITER_AGENT_LICENSE_PUBLIC_KEY || process.env.LICENSE_PUBLIC_KEY || '',
		LICENSE_MACHINE_SALT: process.env.WRITER_AGENT_LICENSE_MACHINE_SALT || 'writer_agent2',
		STATIC_DIR: fs.existsSync(staticDir) ? staticDir : '',
		PYTHONUNBUFFERED: '1',
	};

	apiProcess = spawn(commandInfo.command, commandInfo.args, {
		cwd: commandInfo.cwd,
		env,
		stdio: 'inherit',
	});

	apiProcess.on('exit', (code) => {
		if (!app.isQuiting && code !== 0) {
			dialog.showErrorBox(
				'后端服务已停止',
				`后端进程已退出（code=${code ?? 'unknown'}）。请检查日志或重新启动应用。`,
			);
			app.quit();
		}
	});
}

function killApiProcess() {
	if (!apiProcess || apiProcess.killed) return;
	if (process.platform === 'win32') {
		spawn('taskkill', ['/pid', String(apiProcess.pid), '/f', '/t']);
	} else {
		apiProcess.kill('SIGTERM');
	}
	apiProcess = null;
}

async function createWindow(port) {
	mainWindow = new BrowserWindow({
		width: 1280,
		height: 820,
		backgroundColor: '#0a0a0a',
		webPreferences: {
			contextIsolation: true,
			nodeIntegration: false,
		},
	});

	await mainWindow.loadURL(`http://127.0.0.1:${port}/`);

	mainWindow.on('closed', () => {
		mainWindow = null;
	});
}

app.on('before-quit', () => {
	app.isQuiting = true;
	killApiProcess();
});

app.whenReady().then(async () => {
	const port = (await pickPort()) || 0;
	if (!port) {
		dialog.showErrorBox('端口不可用', '无法找到可用端口，请关闭占用 9761-9790 的进程。');
		app.quit();
		return;
	}
	apiPort = port;
	await startApi(port);

	const ok = await waitForHealthz(port);
	if (!ok) {
		dialog.showErrorBox('后端启动失败', '无法连接后端服务，请检查日志输出。');
		app.quit();
		return;
	}

	await createWindow(port);
});

app.on('window-all-closed', () => {
	if (process.platform !== 'darwin') {
		app.quit();
	}
});

app.on('activate', async () => {
	if (BrowserWindow.getAllWindows().length === 0) {
		const port = apiPort || (await pickPort()) || 9761;
		await createWindow(port);
	}
});
