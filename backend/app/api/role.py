from flask_restful import Resource, reqparse

from app import mark
from app.auth import login_required
from app.models import SysRole, SysMenu, SysRoleMenu, db
from app.response import ResMsg


class RoleResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('role_name', type=str, required=True, help='角色名')
    parser.add_argument('menu_ids', type=int, action='append', help='菜单列表')

    @login_required
    def post(self):
        """创建角色"""
        res = ResMsg()
        args = self.parser.parse_args()
        role_name = args.get("role_name")
        menu_ids = args.get("menu_ids") or []

        if not role_name:
            res.update(code=-1, msg="参数缺失")
            return res.data

        role = SysRole.query.filter(SysRole.role_name == role_name).first()
        if role:
            res.update(code=-1, msg="角色名已存在")
            return res.data

        menu_ids = set(menu_ids)
        if menu_ids:
            query_menu = db.session.query(SysMenu.menu_id).filter(SysMenu.menu_id.in_(menu_ids)).all()
            is_exist_menu = set([item.menu_id for item in query_menu])

            if len(menu_ids) != len(is_exist_menu):
                res.update(code=-1, msg="绑定了不存在的菜单")
                return res.data

        try:
            new = SysRole()
            new.role_name = str(role_name).strip()
            db.session.add(new)
            db.session.flush()
            if menu_ids:
                role_menus = [dict(menu_id=item, role_id=new.role_id) for item in menu_ids]
                db.session.execute(SysRoleMenu.__table__.insert(role_menus))
                db.session.flush()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            res.update(code=-1, msg=str(e))
            return res.data

        return res.data

    @login_required
    def get(self, role_id):
        """获取角色"""
        res = ResMsg()
        if not role_id:
            res.update(code=-1, msg="参数缺失")
            return res.data

        role = SysRole.query.filter(SysRole.role_id == role_id).first()
        if not role:
            res.update(code=-1, msg="角色不存在")
            return res.data

        data = {p.key: getattr(role, p.key) for p in SysRole.__mapper__.iterate_properties}
        res.update(data=data)
        return res.data

    @login_required
    def put(self, role_id):
        """更新角色"""
        res = ResMsg()
        args = self.parser.parse_args()
        role_name = args.get("role_name")
        menu_ids = args.get("menu_ids") or []

        if not role_name or not role_id:
            res.update(code=-1, msg="参数缺失")
            return res.data

        role = SysRole.query.filter(SysRole.role_id == role_id).first()
        if not role:
            res.update(code=-1, msg="角色不存在")
            return res.data

        ist_exist_role_name = SysRole.query.filter(SysRole.role_id != role_id, SysRole.role_name == role_name).first()
        if ist_exist_role_name:
            res.update(code=-1, msg="角色名已存在")
            return res.data

        menu_ids = set(menu_ids)
        if menu_ids:
            query_menu = db.session.query(SysMenu.menu_id).filter(SysMenu.menu_id.in_(menu_ids)).all()
            is_exist_menu = set([item.menu_id for item in query_menu])

            if len(menu_ids) != len(is_exist_menu):
                res.update(code=-1, msg="绑定了不存在的菜单")
                return res.data

        try:

            role.role_name = str(role_name).strip()
            db.session.add(role)
            db.session.flush()
            # 删除原有菜单
            db.session.query(SysRoleMenu).filter(SysRoleMenu.role_id == role_id).delete(synchronize_session=False)
            if menu_ids:
                # 绑定新菜单
                role_menus = [dict(menu_id=item, role_id=role.role_id) for item in menu_ids]
                db.session.execute(SysRoleMenu.__table__.insert(role_menus))
                db.session.flush()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            res.update(code=-1, msg=str(e))
            return res.data

        return res.data


class RoleCheckMenusResource(Resource):

    @login_required
    def get(self, role_id):
        """获取角色已绑定的菜单ID"""
        res = ResMsg()

        if not role_id:
            res.update(code=-1, msg="参数缺失")
            return res.data

        role = SysRole.query.filter(SysRole.role_id == role_id, SysRole.status == mark.Enable).first()
        if not role:
            res.update(code=-1, msg="角色不存在")
            return res.data

        menus = db.session.query(SysRoleMenu.menu_id).filter(SysRoleMenu.role_id == role_id).all()

        data = [item.menu_id for item in menus]
        res.update(data=data)

        return res.data


class RoleStatusResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('status', type=int, required=True, help='角色状态码缺失')

    @login_required
    def put(self, role_id):
        """修改角色状态"""
        res = ResMsg()
        args = self.parser.parse_args()
        status = args.get("status")
        if not role_id or status not in [mark.Enable, mark.Disable]:
            res.update(code=-1, msg="参数缺失")
            return res.data

        role = SysRole.query.filter(SysRole.role_id == role_id).first()
        if not role:
            res.update(code=-1, msg="角色不存在")
            return res.data

        try:
            role.status = status
            db.session.add(role)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            res.update(code=-1, msg=str(e))
            return res.data
        return res.data


class RoleLabelResource(Resource):

    @login_required
    def get(self):
        """获取角色ID名字列表"""
        res = ResMsg()
        roles = db.session.query(SysRole.role_id, SysRole.role_name).all()
        data = [dict(zip(role.keys(), role)) for role in roles]
        res.update(data=data)
        return res.data


class RoleListResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('role_name', type=str, help='角色名')
    parser.add_argument('page', type=int, help='页码')
    parser.add_argument('page_size', type=int, help='条数')

    @login_required
    def get(self):
        """获取角色列表"""

        res = ResMsg()
        args = self.parser.parse_args()
        role_name = args.get("role_name")
        page = args.get("page") or mark.DefaultPage
        page_size = args.get("page_size") or mark.DefaultPageSize

        query = db.session.query(SysRole.role_id, SysRole.role_name, SysRole.status, SysRole.create_time)
        if role_name:
            query = query.filter(SysRole.role_name.like(f'%{role_name}%'))

        total = query.count()
        roles = query.slice((page - 1) * page_size, page * page_size).all()
        data = [dict(zip(role.keys(), role)) for role in roles]
        res.update(data=data)
        res.add_field("total", total)
        return res.data
