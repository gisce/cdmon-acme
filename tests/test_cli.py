from cdmon_acme.cli import build_parser


def test_parser_issue_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["issue", "--domain", "example.com", "--email", "a@b.com"])
    assert args.cmd == "issue"
    assert args.domain == "example.com"
    assert args.lock_file == "./.state/issue.lock"
    assert args.post_hook is None


def test_parser_renew_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["renew", "--domain", "example.com", "--email", "a@b.com"])
    assert args.cmd == "renew"
    assert args.domain == "example.com"


def test_parser_inspect_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["inspect", "--cert", "./certs/fullchain.pem"])
    assert args.cmd == "inspect"
    assert args.cert.endswith("fullchain.pem")
