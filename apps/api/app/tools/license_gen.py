from __future__ import annotations

import argparse
import base64
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _base64url_decode(text: str) -> bytes:
    padded = text + "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _load_private_key(path: str) -> Ed25519PrivateKey:
    raw = Path(path).read_text(encoding="utf-8").strip()
    try:
        key_bytes = _base64url_decode(raw)
    except Exception:
        try:
            key_bytes = bytes.fromhex(raw)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("invalid_private_key_format") from exc
    if len(key_bytes) != 32:
        raise ValueError("invalid_private_key_length")
    return Ed25519PrivateKey.from_private_bytes(key_bytes)


def _write_key(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def _parse_expires_at(value: str | None, days: int | None) -> str | None:
    if value:
        cleaned = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    if days is not None:
        future = datetime.now(tz=timezone.utc) + timedelta(days=days)
        return future.isoformat()
    return None


def cmd_generate_keypair(args: argparse.Namespace) -> int:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)

    priv_text = _base64url_encode(priv_bytes)
    pub_text = _base64url_encode(pub_bytes)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        _write_key(out_dir / "license_private_key.txt", priv_text)
        _write_key(out_dir / "license_public_key.txt", pub_text)
    else:
        print("LICENSE_PRIVATE_KEY=" + priv_text)
        print("LICENSE_PUBLIC_KEY=" + pub_text)
    return 0


def cmd_issue(args: argparse.Namespace) -> int:
    private_key = _load_private_key(args.private_key)
    expires_at = _parse_expires_at(args.expires_at, args.days)

    payload = {
        "license_id": str(uuid.uuid4()),
        "machine_code": args.machine_code.strip(),
        "issued_at": datetime.now(tz=timezone.utc).isoformat(),
        "expires_at": expires_at,
        "features": args.features or {},
    }

    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = private_key.sign(payload_bytes)

    license_code = f"{_base64url_encode(payload_bytes)}.{_base64url_encode(signature)}"
    print(license_code)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline license generator (Ed25519).")
    subparsers = parser.add_subparsers(dest="command")

    gen = subparsers.add_parser("generate-keypair", help="Generate a new keypair.")
    gen.add_argument("--out-dir", help="Directory to write key files.")
    gen.set_defaults(func=cmd_generate_keypair)

    issue = subparsers.add_parser("issue", help="Issue a license code.")
    issue.add_argument("--private-key", required=True, help="Path to base64url/hex private key file.")
    issue.add_argument("--machine-code", required=True, help="Machine code from the client.")
    issue.add_argument("--expires-at", help="Expiry time (ISO8601).")
    issue.add_argument("--days", type=int, help="Expiry in N days from now.")
    issue.add_argument("--features", type=json.loads, default=None, help="JSON features payload.")
    issue.set_defaults(func=cmd_issue)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
