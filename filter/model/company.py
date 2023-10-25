import json

class Company:
    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.founded = ""
        self.size = None
        self.region = None
        self.country = None

    def __str__(self):
        return f"Company: name={self.name}, symbol={self.symbol}, founded={self.founded}, size={self.size}, region={self.region}, country={self.country}"

class CompanyScore:
    def __init__(self, company: Company):
        self.company = company
        self.total_score = 0.0
        self.players_reputation = 0.0
        self.investers_score = 0.0

    def to_json(self):
        return _decode(self)

    @staticmethod
    def from_json(json: str):
        company = Company(i["company"]["name"], i["company"]["symbol"])
        company_score = CompanyScore(company)
        return company_score

    def __str__(self):
        return f"CompanyScore: company={self.company}, total_score={self.total_score}, players_reputation={self.players_reputation}, investers_score={self.investers_score}"

def _decode(company_score: CompanyScore):
    company_json = json.dumps(company_score.company.__dict__)
    company_score.company = None
    company_score_json = json.dumps(company_score.__dict__)
    company_score_json = company_score_json.replace("null", company_json)
    return company_score_json

# TODO: throws error
def company_score_json_to_objects(json_companies: str) -> list:
    companies = []
    for i in json_companies:
        company = Company(i["company"]["name"], i["company"]["symbol"])
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

