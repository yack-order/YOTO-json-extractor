from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.common.exceptions import TimeoutException, WebDriverException
import re

# Constants
REDIRECT_URL = "http://localhost:3000/callback"
ACCESS_TOKEN_PARAM_NAME = 'access_token'
QUERY_STRING_PARAM_REGEX = "[#&]{parameter_name}=([^&#?]*)"

LOGIN_HTML = """
<script src="https://cdn.auth0.com/js/auth0/9.18/auth0.min.js"></script>
<script type="text/javascript">
	var webAuth = new auth0.WebAuth({
		clientID: '90v6OFRB0bKTtpSCqT7edO7rlu9je8nb',
		domain: 'login.yotoplay.com'
	});
	webAuth.authorize({
		responseType: 'token id_token',
		redirectUri: 'http://localhost:3000/callback',
		audience: 'https://api.yotoplay.com',
		scope: 'YOUR_SCOPE'
	});
</script>
"""

def get_access_token():

    opts = webdriver.FirefoxOptions()
    opts.add_argument("--width=500")
    opts.add_argument("--height=700")

    driver = webdriver.Firefox(options=opts)
    driver.get('data:text/html;charset=utf-8,{html_content}'.format(html_content=LOGIN_HTML))
    
    # User must log in within 60 seconds. After that, close the browser window.
    wait = ui.WebDriverWait(driver, 60)

    try:
        wait.until(lambda driver: REDIRECT_URL in driver.current_url)
        url = driver.current_url
        driver.close()
    except TimeoutException:
        print("Timed out waiting for user to log in")
        driver.close()
        return None
    except WebDriverException:
        print("Browser window was closed before user logged in")
        return None

    try:
        return get_query_string_param_by_name(ACCESS_TOKEN_PARAM_NAME, url)
    except:
        print("Failed to parse access token from URL: " + url)
        return None

def get_query_string_param_by_name(name, query_string):
    return re.search(QUERY_STRING_PARAM_REGEX.format(parameter_name=name), query_string).group(1)
