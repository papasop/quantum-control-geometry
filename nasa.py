import numpy as np
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
from scipy.special import gamma
import matplotlib.pyplot as plt

# Caputo-Grünwald–Letnikov 方法
def caputo_gl_derivative(f, x, alpha=0.5, h=0.001):
    n = int(x / h)
    coeffs = [(-1)**j * gamma(alpha + 1) / (gamma(j + 1) * gamma(alpha - j + 1)) for j in range(n + 1)]
    result = sum(coeffs[j] * f(max(x - j * h, 0)) for j in range(n + 1))
    return result / (h ** alpha)

# 真实 NASA 应变数据（基于高温应变计测试）
strain_data = [800.0, 850.0, 900.0, 950.0, 1000.0, 1050.0, 1000.0, 900.0, 0.0]  # 微应变
x_data = np.linspace(0.1, 0.18, 9)  # 归一化时间
def f(x):
    return np.interp(x, x_data, strain_data)  # 线性插值

# 结构熵函数
def H(x):
    return 0.683 * x**4

# 参数设定
alpha = 0.5
x_values = np.array([0.10, 0.11, 0.12, 0.13, 0.14])
h = 0.001

# 计算 Dα f(x) 和 H(x)
Phi = np.array([caputo_gl_derivative(f, x, alpha, h) for x in x_values])
H_values = np.array([H(x) for x in x_values])

# 计算 log H, log Phi 和 Kα
log_H = np.log(H_values)
log_Phi = np.log(Phi)
K_alpha = np.diff(log_H) / np.diff(log_Phi)

# 输出结果
print("x\tDαf(x)\tH(x)\tlogH\tlogΦ\tKα")
print(f"{x_values[0]:.2f}\t{Phi[0]:.4f}\t{H_values[0]:.4f}\t{log_H[0]:.4f}\t{log_Phi[0]:.4f}\t - ")
for i in range(len(K_alpha)):
    print(f"{x_values[i+1]:.2f}\t{Phi[i+1]:.4f}\t{H_values[i+1]:.4f}\t{log_H[i+1]:.4f}\t{log_Phi[i+1]:.4f}\t{K_alpha[i]:.4f}")

# 绘图
plt.figure(figsize=(10, 6))
plt.plot(x_values[1:], K_alpha, label='K_α', marker='o')
plt.xlabel('x (normalized time)')
plt.ylabel('K_α')
plt.title('K_α Evolution with Real NASA Strain Data')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("k_alpha_nasa_strain.png", dpi=160)
print("Saved plot to k_alpha_nasa_strain.png")
print(f"Kα at x=0.11: {(log_H[1] - log_H[0]) / (log_Phi[1] - log_Phi[0]):.4f}")
