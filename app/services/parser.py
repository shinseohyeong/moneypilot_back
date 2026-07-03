from app.services.parsers.parser_shinhan import parse_shinhan
from app.services.parsers.parser_kb import parse_kb

def parse_excel(df, card_name):
    if card_name == "신한카드":
        return parse_shinhan(df)

    elif card_name == "국민카드":
        return parse_kb(df)

    else:
        raise Exception("지원하지 않는 카드사")