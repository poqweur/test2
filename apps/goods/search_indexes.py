#定义模型索引类

from haystack import indexes
#导入对应模型类
from goods.models import GoodSKU
#指定对于某个类的某些数据建立索引
#索引雷鸣:模型类+index
class GoodSKUIndex(indexes.SearchIndex, indexes.Indexable):
    #索引字段use_template指定根据哪些字段生成索引会放在一个文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        #返回模型类
        return GoodSKU

    #建立索引数据
    def index_queryset(self, using=None):
        return self.get_model().objects.all()