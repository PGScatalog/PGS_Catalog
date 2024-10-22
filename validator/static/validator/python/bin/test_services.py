# from validator.config import OLS_EFO_URL, EUROPMC_URL, GWAS_REST_URL
# from pyodide.http import pyfetch
#
#
# async def test_resource(resource_url):
#     response = await pyfetch(resource_url)
#     return response.ok
#
#
# resources = {
#     'OLS_EFO': OLS_EFO_URL
# }
#
# for resource in resources.keys():
#     is_ok = await test_resource(resources.get(resource))
#     print(is_ok)