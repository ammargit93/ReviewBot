from reviewbot.cli import build_parser


async def main():
    parser = build_parser()
    args = parser.parse_args()
    await args.func(args)
