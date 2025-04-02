from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import ddddocr
from selenium.webdriver.support.wait import WebDriverWait
from PIL import Image
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import NoSuchElementException
import schedule
import config
from datetime import datetime
import time

def get_current_time():
    # 获取当前时间
    current_time = datetime.now()
    # 格式化时间，精确到毫秒
    formatted_time = current_time.strftime("%H:%M:%S.%f")
    # 截取到毫秒（3位）
    return formatted_time[:-3]


# 指定ChromeDriver路径
driver_path = config.driver_path
# 指定Chrome浏览器路径
chrome_path = config.chrome_path

username_list = config.username_list
password_list = config.password_list
target_time_list = config.target_time_list
target_venue = config.target_venue
target_venue_list= config.target_venue_list
order_path = config.order_path
prediction_time = config.prediction_time

# 创建Service对象
service = Service(driver_path)
# 创建Options对象并指定Chrome浏览器路径
options = Options()
options.binary_location = chrome_path
order_flag = [False,False,False,False]



def login_with_captcha(driver, username, password, target_time):
    print(f"target-time---{target_time}")
    """
    使用验证码登录函数
    :param driver: webdriver对象
    :param username: 用户名
    :param password: 密码
    """
    while (True): # 由于验证码不能保证每次识别成功，因此要识别到成功为止，也就是要成功登陆为止
        # 截取验证码图片
        captcha_element = driver.find_element(By.XPATH, '//*[@id="validatorCodeOfLogin"]')
        captcha_element.screenshot('captcha.png') # 截取验证码图片，命名为captcha.png
        # img=Image.open('captcha.png')
        # img.show()

        # 使用ddddocr识别验证码
        ocr = ddddocr.DdddOcr()
        with open('captcha.png', 'rb') as f:
            img_bytes = f.read()
        result = ocr.classification(img_bytes)
        print(result) # 打印识别到的验证码

        # 填写用户名和密码
        driver.find_element(By.XPATH, '//*[@id="username"]').send_keys(username)
        driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(password)

        # 输入验证码
        captcha_input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="authCode"]'))
        )
        captcha_input_element.send_keys(result)

        # 点击登录按钮
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="J-login-btn"]'))
        )
        login_button.click()

        # 查看登录状态
        login_state = get_login_state(driver)
        if login_state:
            print(f"{get_current_time()}    登录成功！")
            order(driver, target_time)
            break
        else:
            print("登录失败！")  
            driver.refresh()  # 刷新页面，同时将账户框清空，以便于下次登录进行正确输入
            driver.find_element(By.XPATH, '//*[@id="username"]').clear()
            continue


# 获取登录状态
def get_login_state(driver):
    try:
        # 尝试查找登录失败的提示元素
        login_state_element = driver.find_element(By.XPATH, '//*[@id="msg"]')  #  /html/body/div[2]/div/form/div/div[8]/h6/p
        # 如果找到了该元素，说明登录失败
        return False
    except NoSuchElementException:
        # 如果没有找到该元素，说明登录成功
        return True


# 获取登录状态

def pre_order(target_time,table_element,driver):
        print(f"{get_current_time()}    开始预定场地时间为：  {target_time}")
        venue_elements = table_element.find_elements(By.CLASS_NAME, 'cell')
        filtered_venue_elements = []

        # 获取目标时间段的场地信息
        for venue in venue_elements:
            if venue.get_attribute('data-timer') == target_time:
                filtered_venue_elements.append(venue)
        # target_venue = "场地1"
        # filtered_venue_elements = [venue for venue in venue_elements if venue.get_attribute('data-venue') == target_venue]
        # for element in filtered_venue_elements:
        #     print(element.get_attribute('data-venue'))
        found_venue = False
        for venue in target_venue_list:
            # 查找当前优先级的场地元素
            for element in filtered_venue_elements:
                if element.get_attribute('data-venue') == venue and element.get_attribute('data-canuse') == '1':
                    print("已选择场地", venue)
                    element.click()
                    found_venue = True
                    break
            if found_venue:
                break

        # 获取下订单按钮
        order_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="confirmbutton"]'))
        )
        order_button.click()
        print(f"{get_current_time()}    预定成功")

    # schedule.every().day.at(config.open_html_timne).do(pre_order)
    # 现在直接运行
    

def order(driver, target_time):
    # 获取预定按钮 点击预定按钮，进入场地时间段预约
    predition_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="reserve"]'))
    )
    predition_button.click()

    # 选择指定星期几  选择预约第二天的场地
    select_day = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="daterow"]/li[2]/div[1]'))
    )
    select_day.click()

    # 获取场地表格
    table_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="select_seat"]/div[1]'))
    )
    # 获取表格的HTML内容

    # 获取所有时间段元素
    time_elements = table_element.find_elements(By.CLASS_NAME, 'start')
    # for time_element in time_elements:
    #     print(time_element.text)
    
    # 遍历时间段元素，找到指定时间段
    # target_time = "08:30-09:30"  # 指定时间段
    # found_time = False
    # 找到需要预约的时间段
    # for time_element in time_elements:
    #     if target_time in time_element.text:
    #         found_time = True
    #         print(f"{get_current_time()}找到指定时间段{target_time}")
    #         break
    #     if not found_time:
    #         continue
    # 获取所有场地元素
    schedule.every().day.at(config.prediction_time).do(pre_order(target_time,table_element,driver))
    

def main():
    for i in range(len(username_list)):
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(order_path)
        login_with_captcha(driver=driver, username=username_list[i], password=password_list[i],
                           target_time=target_time_list[i])
        sleep(100)
        break



if __name__ == "__main__":
    schedule.every().day.at(config.open_html_timne).do(main)

    while True:
        schedule.run_pending()
        sleep(1)



    # main()
    

# driver.quit()