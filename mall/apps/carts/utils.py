
import pickle

import base64
from django_redis import get_redis_connection

# 当用户登陆的时候,将cookie数据合并到redis中

#将cookie数据合并到redis中

#有cookie数据
# {sku_id: count:xxx,selected:xxxx}

"""
    {
        1:{count:100,selected:True},
        3:{count:100,selected:False},
    }

"""

#有redis数据
# hash:     cart_userid:        {sku_id:count}
#set:     cart_selected_userid: [sku_id]


"""
    hash:       {2:50,3:50}
    set :       [2]
"""



"""
    1. 获取cookie数据
    cookie:
    {
        1:{count:100,selected:True},
        3:{count:100,selected:False},
    }

    2.获取redis数据
    redis:
    hash:       {2:50,3:50}
    set :       [2]

    #3.初始化工作
    初始化redis的hash数据(把hash数据都获取出来)
    初始化选中的列表    []

    #4.获取到最终的数据
    合并:
    hash:     {
                 2:50,3:50
                }

            [1]
    set:  只需要把 cookie中 选中的拿过来就可以了


    #5.将最终的数据 保存到redis中

    #6.合并之后 cookie数据删除

    产品: sku_id
    如果 cookie中有的商品id,则添加到 redis中来
            count:
    如果redis中没有数量,则使用 cookie的
    如果redis中有数量,cookie中也有:
            1.以redis的为主
            2.以cookie的为主        V
            3.以相加的为主

"""

def merge_cookie_to_redis(request,user,response):
    """

    1.获取cookie数据
    2.获取redis数据
    3.对合并数据做初始化工作
    4.合并
    5.将合并数据保存到redis中
    6.删除cookie数据

    :return:
    """
    # 1.获取cookie数据
    cookie_str = request.COOKIES.get('cart')
    if cookie_str is not None:
        cookie_cart = pickle.loads(base64.b64decode(cookie_str))

        # {sku_id: {count:xxx,selected:xxx}}

        # 2.获取redis数据
        redis_conn = get_redis_connection('cart')
        #hash  -- redis
        # redis 的数据是 bytes类型
        redis_id_count = redis_conn.hgetall('cart_%s'%user.id)
        #  {b'sku_id':b'count'}
        # 3.对合并数据做初始化工作
        merge_cart = {}
        for sku_id,count in redis_id_count.items():
            merge_cart[int(sku_id)]=int(count)
        #初始化选中的id列表
        selected_ids = []
        # 4.合并,需要对 cookie数据进行遍历
        #  { 1:{count:100,selected:True},}
        for sku_id,count_selected_dict in cookie_cart.items():

            # if sku_id not in merge_cart:
            #     merge_cart[sku_id]=count_selected_dict['count']
            # else:
            #     merge_cart[sku_id]=count_selected_dict['count']

            #因为我们的数量是以 cookie为主
            merge_cart[sku_id]=count_selected_dict['count']


            # 判断选中状态
            if count_selected_dict['selected']:
                selected_ids.append(sku_id)



        # 5.将合并数据保存到redis中
        # merge_cart        {sku_id:count,sku_id:count}
        # selected_ids      [1,2,3]
        redis_conn.hmset('cart_%s'%user.id,merge_cart)

        if len(selected_ids) > 0:
            redis_conn.sadd('cart_selected_%s'%user.id,*selected_ids)

        # 6.删除cookie数据
        response.delete_cookie('cart')

        return response


    return response
