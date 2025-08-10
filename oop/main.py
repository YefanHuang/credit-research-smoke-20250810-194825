#!/usr/bin/env python3
"""
信用研究自动化系统主程序
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oop.credit_research_system import CreditResearchSystem

def print_banner():
    """打印系统横幅"""
    print("=" * 60)
    print("        🚀 信用研究自动化系统")
    print("        Credit Research Automation System")
    print("=" * 60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_menu():
    """打印菜单"""
    print("\n📋 可用功能:")
    print("1. 系统状态检查")
    print("2. 系统组件测试")
    print("3. 运行搜索阶段")
    print("4. 运行完整工作流程")
    print("5. 发送测试邮件")
    print("6. 查看系统信息")
    print("0. 退出系统")
    print("-" * 40)

def main():
    """主函数"""
    print_banner()
    
    # 初始化系统
    try:
        system = CreditResearchSystem()
        print("✅ 系统初始化完成")
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return
    
    while True:
        print_menu()
        
        try:
            choice = input("请选择功能 (0-6): ").strip()
            
            if choice == "0":
                print("👋 感谢使用信用研究自动化系统！")
                break
                
            elif choice == "1":
                print("\n🔍 系统状态检查...")
                system.print_system_status()
                
            elif choice == "2":
                print("\n🧪 系统组件测试...")
                test_results = system.test_system()
                
                # 检查测试结果
                if all(test_results.values()):
                    print("🎉 所有组件测试通过！")
                else:
                    failed_components = [comp for comp, success in test_results.items() if not success]
                    print(f"⚠️  以下组件测试失败: {failed_components}")
                
            elif choice == "3":
                print("\n🔍 运行搜索阶段...")
                search_results = system.run_search_phase()
                
                if search_results:
                    print(f"✅ 搜索阶段完成，获得 {len(search_results)} 个结果")
                else:
                    print("❌ 搜索阶段失败")
                
            elif choice == "4":
                print("\n🚀 运行完整工作流程...")
                workflow_result = system.run_full_workflow()
                
                if workflow_result["success"]:
                    print("🎉 完整工作流程执行成功！")
                    system.save_workflow_report(workflow_result)
                else:
                    print(f"❌ 工作流程执行失败: {workflow_result.get('error', '未知错误')}")
                
            elif choice == "5":
                print("\n📧 发送测试邮件...")
                if system.email_manager:
                    success = system.email_manager.send_test_email()
                    if success:
                        print("✅ 测试邮件发送成功")
                    else:
                        print("❌ 测试邮件发送失败")
                else:
                    print("❌ 邮件管理器未初始化")
                
            elif choice == "6":
                print("\n📊 系统信息...")
                system_info = system.get_system_info()
                print(f"组件状态:")
                for component, available in system_info["components"].items():
                    status = "✅ 可用" if available else "❌ 不可用"
                    print(f"  {component}: {status}")
                print(f"配置信息:")
                for key, value in system_info["config"].items():
                    print(f"  {key}: {value}")
                
            else:
                print("❌ 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出系统")
            break
        except Exception as e:
            print(f"❌ 操作失败: {e}")

if __name__ == "__main__":
    main() 