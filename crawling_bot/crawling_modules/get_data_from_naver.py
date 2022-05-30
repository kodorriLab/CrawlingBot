# -*- coding: utf-8 -*-
'''
*******************************************************************************
 * @fileName : get_data_from_naver.py
 * @author   : "Ko Sun Ho"
 * @comment  : naver 쇼핑몰 데이터 크롤링
                조건1 : 해외 상품
                조건2 : 리뷰 1개 이상
                조건3 : 판매자 1개 이상
 * @revision history
 * date            author         comment
 * ----------      ---------      ----------------------------------------------
 * 2022. 05. 30.  Ko Sun Ho       작성
 *******************************************************************************
'''

import requests
import re, time
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd

def timer(start, end):
    hours, rem = divmod(end - start, 3600)
    minutes, seconds = divmod(rem, 60)
    result = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
    return result

class NaverCrawler:

    def __init__(self, base_url, keyword, page_index):
        self.base_url = base_url
        self.keyword = keyword
        self.page_index = page_index
        self.headers = {'User-Agent': UserAgent().chrome}

    def _get_title(self,item):
        title = item.find("div", attrs={"class": "basicList_title__3P9Q7"}).find("a")['title']
        href = item.find("div", attrs={"class": "basicList_title__3P9Q7"}).find("a")['href']
        return title, href

    def _conditionA(self,item):
        '''해외 제품 필터링'''
        flag = False
        overseas = item.find("div",attrs={"class":"basicList_info_area__17Xyo"}).find("div",attrs={"class":"basicList_title__3P9Q7"}).find("button")
        if overseas is not None:
            flag = True
        return flag

    def _conditionB(self,item):
        '''쇼핑몰 카테고리 필터 조건 : 판매자 > 2 '''

        flag = False
        seller = item.find("div", attrs={"class": "basicList_mall_area__lIA7R"})

        sellers = None
        if seller is not None:
            flag = True
            sell_list = item.find("div", attrs={"class": "basicList_mall_area__lIA7R"}).find("ul", attrs={
                "class": 'basicList_mall_list__vIiQw'})

            if sell_list is None:
                flag = False

            if sell_list is not None:
                # li = sell_list.find_all('li').find('a')['title']
                sell_li = sell_list.find_all('li')
                sellers = [i.find('a')['title'] for i in sell_li]

        return flag, sellers

    def _conditionC(self,item):
        '''리뷰 개수 1개 이상'''
        flag = False
        reviews_cnt = 0
        review_check = item.find("div",attrs={"class":"basicList_etc_box__1Jzg6"}).find('a',attrs={"class":"basicList_etc__2uAYO"})
        if review_check is not None:
            if "리뷰" in review_check.get_text():
                reviews_cnt = item.find("div",attrs={"class":"basicList_etc_box__1Jzg6"}).find("em").get_text()
                if int(reviews_cnt.replace(',','')) >= 1:
                    flag = True
        return flag, reviews_cnt


    def _get_text_data(self):

        res_shop_list = []
        for page_i in self.page_index:
            url = self.base_url.format(keyword, page_i, keyword)

            # selenium 을 활용하여 chrome webdriver 정보 로드 -> naver shopping 접속
            browser = webdriver.Chrome('C:/Users/KSH/chromedriver.exe')
            browser.get(url)

            # 무한 스크롤 처리 (웹페이지 스크롤 가장 아래 위치로 내리는 작업)
            pre_scrollHeight = browser.execute_script("return document.body.scrollHeight")  # 이전 페이지 높이
            interval = 2 # sleep time

            while True:
                # 스크롤 가장 아래로 내림
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(interval) #페이지 로딩 대기
                curr_scrollHeight = browser.execute_script("return document.body.scrollHeight") # 현재 높이

                # 현재 높이 과거 높이 비교
                if pre_scrollHeight == curr_scrollHeight:
                    break

                pre_scrollHeight = curr_scrollHeight

            soup = BeautifulSoup(browser.page_source, 'html.parser')

            # class : basicList_item__2XT81 ad 는 제외 (광고)
            items = soup.find_all("li",attrs={"class":'basicList_item__2XT81'})

            for idx, item in enumerate(items):

                title, href = self._get_title(item=item)
                if title == '미용실 헤어샵 트롤리 이동식 선반 웨건 트레이':
                    print('y')

                temp = dict()

                # 해외 판매영역
                if not self._conditionA(item=item):
                    continue

                # 판매자 영역
                flag, sellers = self._conditionB(item=item)
                if not flag:
                    continue

                # 리뷰 영역
                flag, reviews_cnt = self._conditionC(item=item)
                if not flag:
                    continue

                # 제목 영역 - title 추출
                title, href = self._get_title(item=item)
                temp['title'] = title
                temp['reviews_cnt'] = reviews_cnt
                temp['sellers_cnt'] = len(sellers)
                temp['sellers'] = sellers
                temp['href'] = href
                res_shop_list.append(temp)

        return res_shop_list

    def crawling_naver_shop_main(self):
        res_shop_list = self._get_text_data()
        return res_shop_list

if __name__ == '__main__':
    keyword = '머그컵'
    page_index = [i for i in range(1,100)]
    # page_index = [1,2,3,4,5]
    time_s = time.time()
    # base_url = 'https://search.shopping.naver.com/search/all?frm=NVSHATC&origQuery={}&pagingIndex={}&pagingSize=40&productSet=total&query={}&sort=rel&timestamp=&viewType=list'
    base_url = 'https://search.shopping.naver.com/search/all?frm=NVSHATC&origQuery={}&pagingIndex={}&pagingSize=40&productSet=total&query={}&sort=review&timestamp=&viewType=list'

    ins_cra = NaverCrawler(base_url=base_url,page_index=page_index,keyword=keyword)
    res_shop_list = ins_cra.crawling_naver_shop_main()
    shop_df = pd.DataFrame(res_shop_list)
    shop_df.to_csv('C:/Users/KSH/PycharmProjects/CrawlingBot/crawling_bot/resources/' + keyword + '_data.csv',encoding='euc-kr')
    time_e = time.time()
    oper_time = timer(time_s,time_e)
    print('oper time ==> {}'.format(oper_time))










