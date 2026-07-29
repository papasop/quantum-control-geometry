import numpy as np
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
from scipy.special import gamma
import matplotlib.pyplot as plt

# ---- Caputo-Grünwald–Letnikov Fractional Derivative ----
def caputo_gl_derivative(f, x, alpha, h=0.001):
    n = int(x / h)
    coeffs = [(-1)**j * gamma(alpha + 1) / (gamma(j + 1) * gamma(alpha - j + 1)) for j in range(n + 1)]
    result = 0
    for j in range(n + 1):
        x_shift = x - j * h
        result += coeffs[j] * f(x_shift) if x_shift >= 0 else 0
    return result / (h ** alpha)

# ---- Structural Ratio K_alpha Calculator ----
def compute_K_alpha(f, H_func, alpha=0.5, x_start=0.1, x_end=0.14, num_points=5, h=0.001):
    x_vals = np.linspace(x_start, x_end, num_points)
    Phi_vals = np.array([caputo_gl_derivative(f, x, alpha, h) for x in x_vals])
    H_vals = np.array([H_func(x) for x in x_vals])

    log_Phi = np.log(Phi_vals)
    log_H = np.log(H_vals)
    K_alpha = np.diff(log_H) / np.diff(log_Phi)

    # 输出
    print("x\tDαf(x)\tH(x)\tlogH\tlogΦ\tKα")
    print(f"{x_vals[0]:.3f}\t{Phi_vals[0]:.5f}\t{H_vals[0]:.5f}\t{log_H[0]:.5f}\t{log_Phi[0]:.5f}\t - ")
    for i in range(len(K_alpha)):
        print(f"{x_vals[i+1]:.3f}\t{Phi_vals[i+1]:.5f}\t{H_vals[i+1]:.5f}\t{log_H[i+1]:.5f}\t{log_Phi[i+1]:.5f}\t{K_alpha[i]:.5f}")

    # 绘图
    plt.figure(figsize=(10, 6))
    plt.plot(x_vals[1:], K_alpha, marker='o', label=f"K_α (α={alpha})")
    plt.xlabel("x")
    plt.ylabel("K_α")
    plt.title("Structural Ratio K_α vs x")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("k_alpha_structural_ratio.png", dpi=160)
    print("Saved plot to k_alpha_structural_ratio.png")

    return x_vals[1:], K_alpha

# ---- 示例函数设置 ----

# 示例目标函数 f(x) = x^2
def f_example(x):
    return x**2 if x >= 0 else 0

# 示例结构熵函数 H(x) = c * x^4
def H_example(x):
    return 0.683 * x**4

# ---- 调用演示 ----
compute_K_alpha(f=f_example, H_func=H_example, alpha=0.5, x_start=0.1, x_end=0.14, num_points=5)
