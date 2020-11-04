from yuntongxun.ccp_sms import CCP



if __name__ == '__main__':
    # 注意： 测试的短信模板编号为1
    CCP().send_template_sms('18370774724', ['778899', 5], 1)