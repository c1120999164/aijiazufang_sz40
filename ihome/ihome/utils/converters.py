class MobileConverter:
    """自定义路由转换器去匹配手机号"""
    # 定义匹配手机号的正则表达式
    regex = '1[3-9]\d{9}'

    def to_python(self, value):
        # to_python：将匹配结果传递到视图内部时使用
        return str(value)

    def to_url(self, value):
        # to_url：将匹配结果用于反向解析传值时使用
        return str(value)