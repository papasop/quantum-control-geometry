import numpy as np
from scipy.special import gamma

def caputo_gl_derivative(f, x, alpha, h=0.001):
    n = int(x / h)
    coeffs = [(-1)**j * gamma(alpha + 1) / (gamma(j + 1) * gamma(alpha - j + 1)) for j in range(n + 1)]
    result = 0
    for j in range(n + 1):
        result += coeffs[j] * f(x - j * h)
    return result / (h ** alpha)

# 定义函数 f(x) = x^2
def f(x):
    return x**2 if x >= 0 else 0

# 参数
alpha = 0.5
x_values = [0.10, 0.11, 0.12, 0.13, 0.14]
h = 0.001
numerical = [caputo_gl_derivative(f, x, alpha, h) for x in x_values]
analytical = [1.5049 * x**1.5 for x in x_values]
H_values = [0.683 * x**4 for x in x_values]
log_H = np.log(H_values)
log_Phi = np.log(numerical)
K_alpha = np.diff(log_H) / np.diff(log_Phi)

# 输出结果
print("x\t数值结果\t解析结果\t误差\tKα")
for index, (x, num, ana) in enumerate(zip(x_values, numerical, analytical)):
    k_value = "-" if index == 0 else f"{K_alpha[index - 1]:.4f}"
    print(f"{x:.2f}\t{num:.4f}\t{ana:.4f}\t{ana - num:.4f}\t{k_value}")

print(f"Kα at x=0.11: {K_alpha[0]:.4f}")
