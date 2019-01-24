import base64
import pickle

from django_redis import get_redis_connection
# 当用户登陆的时候将cookie数据合并到redis中
#


def merge_cookie_to_redis(request, user, response):
    # 1.获取cookie数据
    cookie_str = request.COOKIES.get('cart')
    if cookie_str is not None:
        cookie_cart = pickle.loads(base64.b64decode(cookie_str))
        # 2.获取redis数据
        redis_conn = get_redis_connection('cart')
        redis_id_count = redis_conn.hgetall('cart_%s' % user.id)
        # 3.对合并数据做初始化工作
        merge_cart = {}
        for sku_id, count in redis_id_count.items():
            merge_cart[int(sku_id)] = int(count)
        # 初始化选中的id列表
        selected_ids = []
        # 4.合并,需要对cookie数据进行遍历
        # {1:{count:100,delected:True}}
        for sku_id, count_selected_dict in cookie_cart.items():
            merge_cart[sku_id] = count_selected_dict['count']
            # 判断选中状态
            if count_selected_dict['selected']:
                selected_ids.append(sku_id)
        # 5.将合并数据保存到redis中
        redis_conn.hmset('cart_%s' % user.id, merge_cart)
        if len(selected_ids) > 0:
            redis_conn.sadd('cart_selected_%s' % user.id, *selected_ids)
        # 6.删除cookie数据
        # response.delete_cookie('cart')
        return response
    return response