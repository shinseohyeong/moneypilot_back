from parsers.parser_shinhan import parse_shinhan
from parsers.parser_kb import parse_kb

PARSERS = {
    "신한카드": parse_shinhan,
    "국민카드": parse_kb
}

def parse_excel(df, card_name):
    parser = PARSERS.get(card_name)
    if not parser:
        raise Exception(
            "지원하지 않는 카드사"
        )

    return parser(df)
