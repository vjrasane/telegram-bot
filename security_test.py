import unittest

#import security

from core.database import Database
#from security import require_permissions, SecurityService, User, Role
from core.security import require_permissions, SecurityService

@require_permissions("test.permission.one")
def single_permission_func():
    pass

@require_permissions("test.permission.one", "test.permission.two")
def dual_permission_func():
    pass
    
@require_permissions("test.permission.three")
def parameter_func(one, two):
    return two, one
    
class SecurityTest(unittest.TestCase):
    def setUp(self):
        Database.initialize('security_test_db')
        SecurityService.instance()
        
    def test(self):
        single_permission_func()
    # def setUp(self):
        # self.no_perm_role = Role("no_perm")
        # self.single_perm_role = Role("single_perm", "test.permission.one")
        # self.single_perm_role_second = Role("single_perm", "test.permission.three")
        # self.dual_perm_role = Role("dual_perm", "test.permission.one", "test.permission.two")
        # self.dual_perm_role_second = Role("dual_perm", "test.permission.one", "test.permission.three")
        
        # self.no_role_user = User("no_role")
        # self.single_role_user = User("single_role", self.single_perm_role)
        # self.single_role_user_second = User("single_role", self.single_perm_role_second)
        # self.single_dual_role_user = User("single_dual_role", self.dual_perm_role)
        # self.single_dual_role_user_second = User("single_dual_role_second", self.dual_perm_role_second)
        # self.combine_role_user = User("dual_role", self.single_perm_role, self.single_perm_role_second)
        
    # def test_single_permission_correct(self):
        # SecurityService.user(self.single_role_user)
        # single_permission_func
        
    # def test_single_permission_correct_dual_role(self):
        # SecurityService.user(self.single_dual_role_user)
        # single_permission_func
        
    # def test_single_permission_correct_combine_role(self):
        # SecurityService.user(self.combine_role_user)
        # single_permission_func
        
    # def test_single_permission_missing(self):
        # SecurityService.user(self.no_role_user)
        # self.assertRaises(security.UnauthorizedException, single_permission_func)
        
    # def test_single_permission_mismatch(self):
        # SecurityService.user(self.single_role_user_second)
        # self.assertRaises(security.UnauthorizedException, single_permission_func)
    
    # def test_dual_permission_correct(self):
        # SecurityService.user(self.single_role_user)
        # dual_permission_func
    
    # def test_dual_permission_correct_dual_role(self):
        # SecurityService.user(self.single_dual_role_user)
        # dual_permission_func
        
    # def test_dual_permission_correct_combine_role(self):
        # SecurityService.user(self.combine_role_user)
        # dual_permission_func
        
    # def test_dual_permission_missing(self):
        # SecurityService.user(self.no_role_user)
        # self.assertRaises(security.UnauthorizedException, dual_permission_func)
        
    # def test_dual_permission_mismatch(self):
        # SecurityService.user(self.single_role_user_second)
        # self.assertRaises(security.UnauthorizedException, dual_permission_func)
        
    # def test_parameter_func_correct(self):
        # SecurityService.user(self.single_role_user_second)
        # self.assertEquals(parameter_func("one", "two"),("two", "one"))
        
    # def test_parameter_func_correct_dual_role(self):
        # SecurityService.user(self.single_dual_role_user_second)
        # self.assertEquals(parameter_func("one", "two"),("two", "one"))
        
    # def test_parameter_func_correct_combine_role(self):
        # SecurityService.user(self.combine_role_user)
        # self.assertEquals(parameter_func("one", "two"),("two", "one"))
        
    # def test_parameter_func_missing(self):
        # SecurityService.user(self.no_role_user)
        # self.assertRaises(security.UnauthorizedException, parameter_func)
        
    # def test_parameter_func_mismatch(self):
        # SecurityService.user(self.single_role_user)
        # self.assertRaises(security.UnauthorizedException, parameter_func)
    
if __name__ == '__main__':
    unittest.main()
