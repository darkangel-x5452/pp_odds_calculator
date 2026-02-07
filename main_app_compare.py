

from companies.company_1.company_1_app import Company1App

from companies.company_2.company_2_app import Company2App
from companies.company_3.company_3_app import Company3App
from utils.logger import logger
from utils.tools import compare_matches

_logger = logger(__name__)

def run_app():
    print("App is running...")
    c1a = Company1App()
    resp_jn = c1a.request_company_url()
    c1a_matches = c1a.get_matches_matches(input_jn=resp_jn)

    c2a = Company2App()
    resp_jn = c2a.request_company_url()
    c2a_matches = c2a.get_matches_matches(input_jn=resp_jn)

    compare_matches(c1a_matches, c2a_matches)

    c3a = Company3App()
    resp_jn = c3a.request_company_url()
    c3a_matches = c3a.get_matches_matches(input_jn=resp_jn)

    compare_matches(c1a_matches, c3a_matches)
    print("App is stopped.")


if __name__ == "__main__":
    _logger.info("Starting the application...")
    run_app()
    _logger.info("Application has stopped.")