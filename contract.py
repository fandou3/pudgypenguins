from eth_account import Account
from eth_account.messages import encode_defunct
from curl_cffi import requests
from datetime import datetime, timezone
import os
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor
import threading

# 配置项
THREAD_COUNT = 2  # 同时运行的线程数

# 用于确保输出不会混乱的锁
print_lock = threading.Lock()

# 初始化colorama
init()

def safe_print(message):
    with print_lock:
        print(message)

def log_success(message):
    safe_print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def log_error(message):
    safe_print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def log_info(message):
    safe_print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def append_to_result(wallet, total, unclaimed):
    with print_lock:
        with open('results.txt', 'a', encoding='utf-8') as f:
            f.write(f"{wallet}: 空投数量为{total}, 未领取数量为{unclaimed}----\n")

def sign_message(private_key, message):
    """
    签名消息
    """
    account = Account.from_key(private_key)
    message_encoded = encode_defunct(text=message)
    signed_message = account.sign_message(message_encoded)
    return signed_message.signature.hex()

def get_auth_message():
    try:
        url = "https://api.clusters.xyz/v0.1/airdrops/pengu/auth/message"
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "origin": "https://claim.pudgypenguins.com",
            "priority": "u=1, i",
            "referer": "https://claim.pudgypenguins.com/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, impersonate="chrome110", timeout=30)
        return response.json()
    except Exception as e:
        log_error(f"获取message失败: {str(e)}")
        return None

def get_auth_token(signature, signingDate, wallet_address):
    try:
        url = "https://api.clusters.xyz/v0.1/airdrops/pengu/auth/token"
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://claim.pudgypenguins.com",
            "priority": "u=1, i",
            "referer": "https://claim.pudgypenguins.com/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        
        data = {
            "signature": signature,
            "signingDate": signingDate,
            "type": "evm",
            "wallet": wallet_address
        }

        response = requests.post(url, headers=headers, json=data, impersonate="chrome110", timeout=30)
        return response.json()
    except Exception as e:
        log_error(f"获取token失败: {str(e)}")
        return None

def get_eligibility(token):
    try:
        url = "https://api.clusters.xyz/v0.1/airdrops/pengu/eligibility"
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://claim.pudgypenguins.com",
            "priority": "u=1, i",
            "referer": "https://claim.pudgypenguins.com/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        
        response = requests.post(url, headers=headers, json=[token], impersonate="chrome110", timeout=30)
        return response.json()
    except Exception as e:
        log_error(f"获取eligibility失败: {str(e)}")
        return None

def process_single_wallet(private_key):
    try:
        # 1. 获取message
        message_response = get_auth_message()
        if not message_response or 'message' not in message_response:
            return
        
        # 2. 签名message
        account = Account.from_key(private_key)
        message = message_response['message']
        signature = sign_message(private_key, message)
        log_info(f"钱包地址: {account.address}")
        
        # 3. 获取token
        token_response = get_auth_token(signature, message_response['signingDate'], account.address)
        if not token_response or 'token' not in token_response:
            return
        
        # 4. 获取eligibility信息
        eligibility = get_eligibility(token_response['token'])
        if eligibility:
            total = eligibility['total']
            unclaimed = eligibility['totalUnclaimed']
            log_success(f"钱包 {account.address} 空投数量为：{total}")
            log_success(f"钱包 {account.address} 未领取数量为：{unclaimed}")
            append_to_result(account.address, total, unclaimed)
            
    except Exception as e:
        log_error(f"处理钱包时发生错误: {str(e)}")
    finally:
        with print_lock:
            print("-" * 50)

def main():
    if not os.path.exists('private_keys.txt'):
        log_error("请创建private_keys.txt文件并输入私钥（每行一个）")
        return
        
    with open('private_keys.txt', 'r') as f:
        private_keys = [line.strip() for line in f if line.strip()]
    
    # 处理私钥格式
    private_keys = [key for key in private_keys]
    
    log_info(f"总共读取到 {len(private_keys)} 个钱包，使用 {THREAD_COUNT} 个线程处理")
    
    # 使用线程池处理所有钱包
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        executor.map(process_single_wallet, private_keys)

if __name__ == "__main__":
    main()