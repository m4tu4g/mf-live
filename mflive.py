import httpx
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


class MFLive:
    def __init__(self, *args: list):
        self.MF_SEARCH_URL = os.getenv("MF_SEARCH_URL")

        # stale by 30 mins
        # self.STOCK_SEARCH_URL = os.getenv("STOCK_SEARCH_URL")

        # live, when logged in
        self.NSE_STOCK_SEARCH_URL = os.getenv("NSE_STOCK_SEARCH_URL")
        # todo: Use BSE when not listed on NSE
        self.BSE_STOCK_SEARCH_URL = os.getenv("BSE_STOCK_SEARCH_URL")

        # public search (not listing some stocks on full search, only with partial search)
        self.STOCK_CODE_SEARCH_URL = os.getenv("STOCK_CODE_SEARCH_URL")

        # when logged in, auth is checked
        # self.STOCK_CODE_SEARCH_URL = os.getenv("STOCK_CODE_USER_SEARCH_URL")

        # cache/db
        self.search_id_to_code_map = {
            "jio-financial-services-ltd": "JIOFIN",
            "reliance-industries-ltd": "RELIANCE",
        }

        self.mfs = args

        self.httpx_client = httpx.AsyncClient()


    async def get_holdings(self, mf_name):
        url = self.MF_SEARCH_URL + "/" + mf_name
        resp = await self.httpx_client.get(url)
        return resp.json().get("holdings")


    async def get_stock_data(self, holding, stock_code, dcp=False):
        url = self.NSE_STOCK_SEARCH_URL.format(stock_code=stock_code)
        try:
            resp = await self.httpx_client.get(url)
            resp = resp.json()
        except:
            logging.debug(f"Failed getting data of {stock_code}")
            logging.debug(f"URL: {url}")
            self.not_found[holding['company_name']] = holding['corpus_per']
            return 0 if dcp else {"error": "not found"}
        if dcp:
            return resp["dayChangePerc"]
        return resp

    @staticmethod
    def sanitize_name(query):
        query = query.replace(",", "").replace("'", "").replace("&", "")
        query = query.replace("-", "") #.replace("(", "").replace(")", "")
        return " ".join(query.split(' ')[:3])

    async def get_stock_code(self, holding, search_id):
        comp_name = holding['company_name']
        sanitized_name = MFLive.sanitize_name(comp_name)
        params = {"page": 0, "query": sanitized_name, "web": True}
        try:
            resp = await self.httpx_client.get(self.STOCK_CODE_SEARCH_URL, params=params)
            resp = resp.json()
            match_field = resp['data']['content'][0]
        except:
            logging.debug(f"Failed getting stock code of {comp_name} (Optimised {sanitized_name})")
            self.not_found[comp_name] = holding['corpus_per']
            return "FAILED"

        title = match_field['title']
        if comp_name.lower() !=  title.lower():
            logging.debug(f"{comp_name} != {title} but setting {match_field['nse_scrip_code']}")
            self.not_matched[comp_name] = [title, holding['corpus_per']]
        return match_field['nse_scrip_code']


    async def get_stock_dcp(self, holding):
        comp_name = holding['company_name']
        corp_perc = holding['corpus_per']
        if search_id := holding.get("stock_search_id"):
            stock_code = await self.get_stock_code(holding, search_id)
            if stock_code == "FAILED":
                return (comp_name, 0, corp_perc)
            stock_dcp = await self.get_stock_data(holding, stock_code, dcp=True)
            return (stock_code, stock_dcp, corp_perc)
        else:
            return (comp_name, 0, corp_perc)


    async def get_info(self):
        response = []
        
        for mf in self.mfs:
            self.not_found = {}
            self.not_matched = {}

            holdings = await self.get_holdings(mf)
            
            tasks = [asyncio.create_task(self.get_stock_dcp(holding)) for holding in holdings]
            
            percs = await asyncio.gather(*tasks)

            change_wrt_corpus, corp_percs = [], []

            for stock_code, stock_dcp, corp_perc in percs:
                change_wrt_corpus.append(corp_perc * stock_dcp)
                corp_percs.append(corp_perc)

            response.append({
                "fund" : mf,
                "day_change_percentage" : sum(change_wrt_corpus)/sum(corp_percs),
                "not_found" : self.not_found,
                "not_matched" : self.not_matched
            })

        return response

    async def __del__ (self):
        await self.httpx_client.aclose()


if __name__ == "__main__":
    import colorama

    colorama.init(autoreset=True)
    
    mfs = [
        "motilal-oswal-most-focused-midcap-30-fund-direct-growth",
        "quant-small-cap-fund-direct-plan-growth",
        "axis-small-cap-fund-direct-growth",
        "parag-parikh-long-term-value-fund-direct-growth",
        "icici-prudential-nifty-index-fund-direct-growth",
        # "icici-prudential-nifty-next-50-index-fund-direct-growth",
    ]

    mflive = MFLive(*mfs)
    mfs_info = asyncio.run(mflive.get_info())
    for mf in mfs_info:
        print("MF : ", colorama.Fore.YELLOW + mf['fund'])
        print("estimated day change : ", colorama.Fore.GREEN +  str(mf["day_change_percentage"]))
        print("not found : ", colorama.Fore.RED + str(mf["not_found"]))
        print("not matched : ", colorama.Fore.RED + str(mf["not_matched"]))
        print("-------------------")