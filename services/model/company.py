import json


class Company:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol


class CompanyScore:
    def __init__(self, company: Company):
        self.company = company
        self.score = 0.0
        self.evaluator_name = ""

    def to_json(self):
        return _decode(self)


def _decode(company_score: CompanyScore):
    d = company_score.__dict__
    d["company"] = d["company"].__dict__
    company_score_json = json.dumps(d)
    return company_score_json


def company_score_json_to_objects(json_companies: list) -> list:
    companies = []
    for json_comp in json_companies:
        company = Company(json_comp["company"]["name"], json_comp["company"]["symbol"])
        company_score = CompanyScore(company)
        companies.append(company_score)
    return companies


def company_score_objects_to_json(companies: list) -> str:
    response = "["
    for i in range(len(companies)):
        json_company = companies[i].to_json()
        response += json_company
        if i == len(companies) - 1:
            continue
        else:
            response += ", "
    response += "]"

    return response
