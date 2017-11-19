from django.contrib import admin
from goods.models import GoodsType,GoodSKU,Goods,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
# Register your models here.
# class Good(admin.ModelAdmin):
#     list_display = ['name']
#
# class image(admin.ModelAdmin):
#     list_display = ['image']

class 根据表中的数据生成新的静态页面(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        '''新增或修改表中数据时被调用'''
        #调用父类的方法
        super().save_model(request,obj,form,change)
        #重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        '''删除表中数据被调用'''
        #调用父类方法
        super().delete_model(request, obj)
        # 重新生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

admin.site.register(GoodsType)
admin.site.register(GoodSKU,Good)
admin.site.register(Goods,Good)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexTypeGoodsBanner)
admin.site.register(IndexPromotionBanner,根据表中的数据生成新的静态页面)