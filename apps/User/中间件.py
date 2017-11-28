#注册中间件
class TestMiddleware(object):
    def __init__(self):
        print('测试init初始化前')

    def process_request(self,request):
        print('测试process_request请求响应前')

    def process_view(self,request,view_func,view_args,view_kwargs):
        print('测试process_view视图响应前')

    def process_template_response(self,request,response):
        print('测试process_template_response模板响应前')
        return response

    def process_response(self,request,response):
        print('测试process_response响应后')
        return response

    # def process_exception(self,request,exception):
    #     print('测试process_exception视图抛出的异常')