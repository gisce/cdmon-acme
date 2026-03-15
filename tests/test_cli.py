from cdmon_acme.cli import build_parser


def test_parser_issue_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["issue", "--domain", "example.com", "--email", "a@b.com"])
    assert args.cmd == "issue"
    assert args.domain == "example.com"
