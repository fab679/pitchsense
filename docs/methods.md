# PitchSense Analytics Methods & Metric Definitions

This document describes the deterministic Scout metrics and trajectory-to-ground-truth distance comparison implemented by PitchSense. The app does not run computer vision on image or video frames.

---

## 1. Expected Goals ($xG$)

PitchSense uses a logistic formulation modeling the probability of an unblocked shot on goal being scored based on shot distance and visual goal-mouth angle.

$$\text{logit}(p) = \beta_0 + \beta_{\text{dist}} \cdot d + \beta_{\text{angle}} \cdot \theta + \beta_{\text{header}} \cdot \mathbb{I}_{\text{header}}$$

$$xG = \frac{1}{1 + e^{-\text{logit}(p)}}$$

Where:
* $d$: Euclidean distance to goal center: $\sqrt{(105 - x)^2 + (34 - y)^2}$ meters.
* $\theta$: Subtended goal angle: $|\arctan_2(y - y_{\text{top}}, 105 - x) - \arctan_2(y - y_{\text{bot}}, 105 - x)|$ radians, where goal posts are at $y_{\text{top}} = 30.34$ and $y_{\text{bot}} = 37.66$.
* Calibrated coefficients: $\beta_0 = -0.80$, $\beta_{\text{dist}} = -0.11$, $\beta_{\text{angle}} = 1.30$.
* Monotonic bounds: $xG \in [0.015, 0.950]$.

---

## 2. Pass Difficulty Index

Quantifies the execution difficulty of an intended pass on a 0 to 100 scale:

$$\text{Difficulty} = \text{clamp}\Big(1.4 \cdot d + 35.0 \cdot P_{\text{receipt}} + 0.8 \cdot \max(0, \Delta x),\, [5.0,\, 99.0]\Big)$$

Where:
* $d$: Pass length (meters).
* $P_{\text{receipt}}$: Local pressure index $[0..1]$ exerted by defenders within a 10m envelope.
* $\Delta x$: Forward progression towards opponent goal ($x_{\text{end}} - x_{\text{start}}$).

---

## 3. Rolling Momentum Differential

Measures shift in territorial and offensive threat using an Exponentially Weighted Moving Average (EWMA) across a sliding 5-minute window:

$$\text{Threat}(e) = \begin{cases} 
7.0 & \text{if } e = \text{goal} \\
3.5 & \text{if } e = \text{shot} \\
1.8 & \text{if } e = \text{tackle} \\
1.0 & \text{otherwise}
\end{cases}$$

$$\Delta_{\text{raw}} = \frac{\sum_{e \in \text{SAL}} \text{Threat}(e) - \sum_{e \in \text{BRA}} \text{Threat}(e)}{\sum_{e} \text{Threat}(e)}$$

$$\text{Momentum}_t = 0.85 \cdot \text{Momentum}_{t-1} + 0.15 \cdot \Delta_{\text{raw}}$$

Bounded within $[-1.0, 1.0]$. Positive values denote Saltmarsh Rovers dominance; negative values denote Brackfield Athletic dominance.

---

## 4. Control Index & Chaos Index

* **Control Index ($[0..1]$)**: Reflects team possession efficiency and ability to sustain passing sequences reaching the final third ($x \ge 70\text{m}$).
* **Chaos Index ($[0..1]$)**: Ratio of turnovers, tackles, and duel disruptions within the attacking third over the rolling 7-minute match window. Higher values indicate broken play and transition phases.

---

## 5. Trajectory Distance Agreement

The trajectory scout receives generated start/end coordinates from each synthetic event; it does not observe or process image/video frames and does not independently detect or classify events.

1. **Velocity Tracking**:
   $$\text{Speed}_{\text{km/h}} = \min\left(120,\, \max\left(20,\, \frac{d_{\text{observed}}}{\Delta t} \cdot 3.6\right)\right)$$
2. **Ground Truth Reconciliation**:
   An observed detection is counted as an exact agreement if:
   $$|d_{\text{observed}} - d_{\text{truth}}| \le \tau_{\text{tolerance}} \quad (\tau = 2.0\text{ meters})$$
3. **Reported Agreement Percentage**:
   $$\text{Agreement Rate} = \frac{N_{\text{agreed}}}{N_{\text{total}}} \times 100\%$$
   Live agreement rate is presented directly on the Producer Desk on camera.
