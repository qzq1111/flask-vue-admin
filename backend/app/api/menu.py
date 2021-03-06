from flask_restful import Resource, reqparse

from app.auth import login_required
from app.models import SysMenu, db
from app.response import ResMsg
from app.utils import BuildMenuTree


class MenuResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('menu_name', type=str, required=True, help='组件菜单名')
    parser.add_argument('menu_title', type=str, required=True, help='显示的菜单名')
    parser.add_argument('parent_id', type=int, required=True, help='父菜单ID')
    parser.add_argument('order_num', type=int, required=True, help='显示顺序')
    parser.add_argument('path', type=str, required=True, help='路由地址')
    parser.add_argument('component', type=str, required=True, help='组件地址')
    parser.add_argument('menu_type', type=str, required=True, help='菜单类型 M目录 C菜单 F按钮')
    parser.add_argument('status', type=int, required=True, help='菜单状态1显示 0隐藏')
    parser.add_argument('visible', type=int, required=True, help='菜单状态1正常 0停用')
    parser.add_argument('perms', type=str, required=True, help='权限标识')
    parser.add_argument('icon', type=str, required=True, help='菜单图标')
    parser.add_argument('remark', type=str, required=True, help='备注')

    @login_required
    def post(self):
        """创建菜单"""
        res = ResMsg()
        args = self.parser.parse_args()
        parent_id = args.get("parent_id")
        # 判断父级ID是否存在
        if parent_id:
            query = db.session.query(SysMenu).filter(SysMenu.menu_id == parent_id).first()
            if not query:
                res.update(code=-1, msg="父菜单不存在")
                return res.data
        else:
            args["component"] = "Layout"

        try:
            new = SysMenu(**args)
            db.session.add(new)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            res.update(code=-1, msg=str(e))

        return res.data

    @login_required
    def get(self, menu_id):
        """获取菜单"""
        res = ResMsg()
        if not menu_id:
            res.update(code=-1, msg="参数缺失")
            return res.data

        query = db.session.query(SysMenu).filter(SysMenu.menu_id == menu_id).first()
        if not query:
            res.update(code=-1, msg="菜单栏不存在")
            return res.data

        data = {p.key: getattr(query, p.key) for p in SysMenu.__mapper__.iterate_properties}
        res.update(data=data)
        return res.data

    @login_required
    def put(self, menu_id):
        """修改菜单"""
        res = ResMsg()
        args = self.parser.parse_args()
        menu_name = args.get("menu_name")
        menu_title = args.get("menu_title")
        parent_id = args.get("parent_id")
        order_num = args.get("order_num")
        path = args.get("path")
        component = args.get("component")
        menu_type = args.get("menu_type")
        status = args.get("status")
        visible = args.get("visible")
        perms = args.get("perms")
        icon = args.get("icon")
        remark = args.get("remark")

        if not menu_id:
            res.update(code=-1, msg="参数缺失")
            return res.data

        # 判断父级ID是否存在
        if parent_id:
            query = db.session.query(SysMenu).filter(SysMenu.menu_id == parent_id).first()
            if not query:
                res.update(code=-1, msg="父菜单不存在")
                return res.data

        menu = db.session.query(SysMenu).filter(SysMenu.menu_id == menu_id).first()
        if not menu:
            res.update(code=-1, msg="菜单不存在")
            return res.data

        try:
            menu.menu_name = menu_name
            menu.menu_title = menu_title
            menu.parent_id = parent_id
            menu.order_num = order_num
            menu.path = path
            menu.component = component
            menu.menu_type = menu_type
            menu.status = status
            menu.visible = visible
            menu.perms = perms
            menu.icon = icon
            menu.remark = remark
            db.session.add(menu)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            res.update(code=-1, msg=str(e))
        return res.data

    @login_required
    def delete(self, menu_id):
        """删除菜单"""
        res = ResMsg()
        if not menu_id:
            res.update(code=-1, msg="参数缺失")
            return res.data

        # 是否存在子菜单
        is_exist_children = db.session.query(SysMenu).filter(SysMenu.parent_id == menu_id).first()
        if is_exist_children:
            res.update(code=-1, msg="存在子菜单无法删除")
            return res.data

        query = db.session.query(SysMenu).filter(SysMenu.menu_id == menu_id).first()
        if not query:
            return res.data

        try:
            db.session.delete(query)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            res.update(code=-1, msg=str(e))

        return res.data


class GetMenuList(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('menu_title', type=str, required=False, help='显示的菜单名')

    @login_required
    def get(self):
        """获取所有菜单列表"""
        res = ResMsg()
        args = self.parser.parse_args()
        menu_title = args.get("menu_title")

        query = db.session.query(SysMenu)
        if menu_title:
            query = query.filter(SysMenu.menu_title.like(f"%{menu_title}%"))
        query = query.all()
        data = list(map(lambda x: {p.key: getattr(x, p.key) for p in SysMenu.__mapper__.iterate_properties}, query))
        res.update(data=data)
        return res.data


class SelectMenus(Resource):

    @login_required
    def get(self):
        """获取菜单树结构，用于赋权"""
        res = ResMsg()
        query = db.session.query(SysMenu).all()
        tree = BuildMenuTree(query)
        data = tree.label_tree()
        res.update(data=data)
        return res.data
