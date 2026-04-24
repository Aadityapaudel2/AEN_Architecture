\subsection{YaRN scaling}
\label{subsec:yarn-scaling}

AEN relies on long-context Qwen-family sessions to keep role memory, certification probes, current problem state, peer transcripts, and controller state simultaneously available in-session. Yet another Rotary Position Embedding Extension (YaRN)-style scaling is used here as an enabling mechanism for that long-context runtime-memory substrate, not as a standalone theorem of improved reasoning quality \citep{peng2023yarn,yang2025qwen25oneM}.

For an attention head of even dimension \(d_h=2J\), decompose each query/key vector into \(J\) two-dimensional blocks. RoPE rotates each block independently \citep{su2021roformer}. For a scalar angle \(\phi\in\mathbb R\), define the planar rotation matrix
\begin{equation}
\mathbf Q(\phi)
:=
\begin{bmatrix}
\cos \phi & -\sin \phi\\
\sin \phi & \cos \phi
\end{bmatrix}.
\label{eq:yarn-Q}
\end{equation}
For RoPE frequency \(\theta_j\) and token position \(m\in\mathbb Z\), the \(j\)-th pair rotation is
\begin{equation}
\mathbf R_{\theta_j}(m)
:=
\mathbf Q(m\theta_j),
\qquad j=1,\dots,J.
\label{eq:yarn-pair-rotation}
\end{equation}
The full RoPE operator is the block-diagonal matrix
\begin{equation}
\mathcal R_{\boldsymbol\theta}(m)
:=
\operatorname{diag}\!\bigl(
\mathbf R_{\theta_1}(m),\dots,\mathbf R_{\theta_J}(m)
\bigr),
\qquad
\boldsymbol\theta=(\theta_1,\dots,\theta_J).
\label{eq:yarn-full-rope}
\end{equation}

Let \(L\) denote the pretrained context length, let \(L'=sL\) be the target extended context length with scale factor \(s>1\), and define the wavelength of pair \(j\) by
\begin{equation}
\lambda_j := \frac{2\pi}{\theta_j}.
\label{eq:yarn-wavelength}
\end{equation}
Following the Neural Tangent Kernel (NTK)-by-parts interpolation used in YaRN \citep{peng2023yarn}, define the rotation-count ratio
\begin{equation}
r_j := \frac{L}{\lambda_j} = \frac{L\theta_j}{2\pi},
\label{eq:yarn-rotation-ratio}
\end{equation}
the ramp function
\begin{equation}
\gamma(r)
:=
\begin{cases}
0, & r<\alpha,\\[3pt]
1, & r>\beta,\\[3pt]
\dfrac{r-\alpha}{\beta-\alpha}, & \alpha \le r \le \beta,
\end{cases}
\qquad \alpha<\beta,
\label{eq:yarn-ramp}
\end{equation}
and the YaRN frequency map
\begin{equation}
\theta'_j
=
h_s(\theta_j)
:=
\bigl(1-\gamma(r_j)\bigr)\frac{\theta_j}{s}
+
\gamma(r_j)\theta_j.
\label{eq:yarn-frequency-map}
\end{equation}
Set \(\boldsymbol\theta'=(\theta'_1,\dots,\theta'_J)\), and define the transformed RoPE operator
\begin{equation}
\mathcal R_s(m)
:=
\mathcal R_{\boldsymbol\theta'}(m)
=
\operatorname{diag}\!\bigl(
\mathbf R_{\theta'_1}(m),\dots,\mathbf R_{\theta'_J}(m)
\bigr).
\label{eq:yarn-scaled-operator}
\end{equation}
Equivalently, YaRN acts blockwise as
\begin{equation}
T_s:\mathbf R_{\theta_j}(m)\longmapsto \mathbf R_{\theta'_j}(m).
\label{eq:yarn-block-transform}
\end{equation}
For later use, define the continuous phase budget of angular frequency \(\vartheta\) over a window of length \(W>0\) by
\begin{equation}
\Phi(W;\vartheta) := W\vartheta.
\label{eq:yarn-phase-budget}
\end{equation}

\begin{lemma}[Algebra of planar rotations]
\label{lem:yarn-rotation-identities}
For all \(\phi,\psi\in\mathbb R\),
\begin{align}
\mathbf Q(\phi)^\top &= \mathbf Q(-\phi), \label{eq:yarn-transpose}\\
\mathbf Q(\phi)\mathbf Q(\psi) &= \mathbf Q(\phi+\psi), \label{eq:yarn-composition}\\
\mathbf Q(\phi)^\top \mathbf Q(\psi) &= \mathbf Q(\psi-\phi). \label{eq:yarn-relative}
\end{align}
In particular,
\begin{equation}
\mathbf Q(\phi)^\top \mathbf Q(\phi)=\mathbf I_2
\qquad\text{and}\qquad
\det \mathbf Q(\phi)=1,
\label{eq:yarn-orthogonal}
\end{equation}
so \(\mathbf Q(\phi)\in \mathrm{SO}(2)\).
\end{lemma}

\begin{proof}
Equation~\eqref{eq:yarn-transpose} is immediate from the definition \eqref{eq:yarn-Q}. Direct multiplication gives
\[
\mathbf Q(\phi)\mathbf Q(\psi)
=
\begin{bmatrix}
\cos\phi\cos\psi-\sin\phi\sin\psi &
-(\cos\phi\sin\psi+\sin\phi\cos\psi)\\
\sin\phi\cos\psi+\cos\phi\sin\psi &
\cos\phi\cos\psi-\sin\phi\sin\psi
\end{bmatrix}.
\]
Using the trigonometric addition identities
\[
\cos(\phi+\psi)=\cos\phi\cos\psi-\sin\phi\sin\psi,
\qquad
\sin(\phi+\psi)=\sin\phi\cos\psi+\cos\phi\sin\psi,
\]
this matrix is exactly \(\mathbf Q(\phi+\psi)\), proving \eqref{eq:yarn-composition}. Then
\[
\mathbf Q(\phi)^\top \mathbf Q(\psi)
=
\mathbf Q(-\phi)\mathbf Q(\psi)
=
\mathbf Q(\psi-\phi),
\]
which proves \eqref{eq:yarn-relative}. Setting \(\psi=\phi\) yields
\[
\mathbf Q(\phi)^\top \mathbf Q(\phi)=\mathbf Q(0)=\mathbf I_2.
\]
Finally,
\[
\det \mathbf Q(\phi)
=
\cos^2\phi+\sin^2\phi
=
1.
\]
Hence \(\mathbf Q(\phi)\in \mathrm{SO}(2)\).
\end{proof}

\begin{proposition}[Operator properties of YaRN-scaled RoPE]
\label{prop:yarn-operator}
Let \(q=(q_1^\top,\dots,q_J^\top)^\top\) and \(k=(k_1^\top,\dots,k_J^\top)^\top\in\mathbb R^{d_h}\), where \(q_j,k_j\in\mathbb R^2\). Then, for every \(m,n\in\mathbb Z\),
\begin{enumerate}
    \item \textbf{Orthogonality and non-expansiveness.}
    \begin{equation}
    \mathcal R_s(m)^\top \mathcal R_s(m)=\mathbf I_{d_h}.
    \label{eq:yarn-full-orthogonality}
    \end{equation}
    Consequently,
    \begin{equation}
    \|\mathcal R_s(m)x\|_2=\|x\|_2
    \quad \forall x\in\mathbb R^{d_h},
    \qquad
    \|\mathcal R_s(m)\|_{2\to 2}=1.
    \label{eq:yarn-nonexpansive}
    \end{equation}

    \item \textbf{Preservation of the relative-position kernel form.}
    \begin{equation}
    \mathcal R_s(m)^\top \mathcal R_s(n)=\mathcal R_s(n-m).
    \label{eq:yarn-full-relative}
    \end{equation}
    Consequently,
    \begin{align}
    \left\langle \mathcal R_s(m)q,\mathcal R_s(n)k\right\rangle
    &=
    \left\langle q,\mathcal R_s(n-m)k\right\rangle \label{eq:yarn-inner-product-relative}\\
    &=
    \sum_{j=1}^{J} q_j^\top \mathbf Q\!\bigl((n-m)\theta'_j\bigr)k_j.
    \label{eq:yarn-blockwise-relative}
    \end{align}

    \item \textbf{High-frequency endpoint invariance.}
    If \(r_j\ge \beta\), then
    \begin{equation}
    \theta'_j=\theta_j
    \qquad\text{and hence}\qquad
    \mathbf R_{\theta'_j}(m)=\mathbf R_{\theta_j}(m)
    \quad \forall m\in\mathbb Z.
    \label{eq:yarn-high-freq-invariance}
    \end{equation}

    \item \textbf{Low-frequency phase-budget preservation over the extended window.}
    If \(r_j\le \alpha\), then
    \begin{equation}
    \theta'_j=\frac{\theta_j}{s},
    \qquad
    \lambda'_j:=\frac{2\pi}{\theta'_j}=s\lambda_j,
    \label{eq:yarn-low-freq-rescaling}
    \end{equation}
    and therefore
    \begin{equation}
    \frac{L'}{\lambda'_j}=\frac{L}{\lambda_j},
    \qquad
    \Phi(L';\theta'_j)=\Phi(L;\theta_j).
    \label{eq:yarn-phase-preservation}
    \end{equation}
\end{enumerate}
\end{proposition}

\begin{proof}
Because \(\mathcal R_s(m)\) is block diagonal with blocks \(\mathbf Q(m\theta'_j)\), Lemma~\ref{lem:yarn-rotation-identities} applies to each block separately.

For item~1,
\[
\mathcal R_s(m)^\top \mathcal R_s(m)
=
\operatorname{diag}\!\bigl(
\mathbf Q(m\theta'_1)^\top \mathbf Q(m\theta'_1),
\dots,
\mathbf Q(m\theta'_J)^\top \mathbf Q(m\theta'_J)
\bigr)
=
\operatorname{diag}(\mathbf I_2,\dots,\mathbf I_2)
=
\mathbf I_{d_h},
\]
which proves \eqref{eq:yarn-full-orthogonality}. Hence, for any \(x\in\mathbb R^{d_h}\),
\[
\|\mathcal R_s(m)x\|_2^2
=
x^\top \mathcal R_s(m)^\top \mathcal R_s(m)x
=
x^\top x
=
\|x\|_2^2,
\]
so \(\|\mathcal R_s(m)x\|_2=\|x\|_2\). Taking the supremum over \(\|x\|_2=1\) gives \(\|\mathcal R_s(m)\|_{2\to 2}=1\), proving \eqref{eq:yarn-nonexpansive}.

For item~2,
\[
\mathcal R_s(m)^\top \mathcal R_s(n)
=
\operatorname{diag}\!\bigl(
\mathbf Q(m\theta'_1)^\top \mathbf Q(n\theta'_1),
\dots,
\mathbf Q(m\theta'_J)^\top \mathbf Q(n\theta'_J)
\bigr).
\]
Applying \eqref{eq:yarn-relative} blockwise yields
\[
\mathcal R_s(m)^\top \mathcal R_s(n)
=
\operatorname{diag}\!\bigl(
\mathbf Q((n-m)\theta'_1),
\dots,
\mathbf Q((n-m)\theta'_J)
\bigr)
=
\mathcal R_s(n-m),
\]
which proves \eqref{eq:yarn-full-relative}. Then
\[
\left\langle \mathcal R_s(m)q,\mathcal R_s(n)k\right\rangle
=
q^\top \mathcal R_s(m)^\top \mathcal R_s(n)k
=
q^\top \mathcal R_s(n-m)k,
\]
proving \eqref{eq:yarn-inner-product-relative}. Expanding the block-diagonal action gives
\[
q^\top \mathcal R_s(n-m)k
=
\sum_{j=1}^{J} q_j^\top \mathbf Q\!\bigl((n-m)\theta'_j\bigr)k_j,
\]
which is \eqref{eq:yarn-blockwise-relative}.

For item~3, suppose \(r_j\ge \beta\). By \eqref{eq:yarn-ramp}, \(\gamma(\beta)=1\) from the interpolation branch and \(\gamma(r)=1\) for all \(r>\beta\), so \(\gamma(r_j)=1\). Substituting into \eqref{eq:yarn-frequency-map},
\[
\theta'_j
=
\bigl(1-\gamma(r_j)\bigr)\frac{\theta_j}{s}
+
\gamma(r_j)\theta_j
=
(1-1)\frac{\theta_j}{s}+1\cdot\theta_j
=
\theta_j.
\]
Therefore \(\mathbf R_{\theta'_j}(m)=\mathbf R_{\theta_j}(m)\) for all \(m\in\mathbb Z\), which proves \eqref{eq:yarn-high-freq-invariance}.

For item~4, suppose \(r_j\le \alpha\). By \eqref{eq:yarn-ramp}, \(\gamma(\alpha)=0\) from the interpolation branch and \(\gamma(r)=0\) for all \(r<\alpha\), so \(\gamma(r_j)=0\). Substituting into \eqref{eq:yarn-frequency-map},
\[
\theta'_j
=
\bigl(1-\gamma(r_j)\bigr)\frac{\theta_j}{s}
+
\gamma(r_j)\theta_j
=
\frac{\theta_j}{s}.
\]
Hence
\[
\lambda'_j
=
\frac{2\pi}{\theta'_j}
=
\frac{2\pi}{\theta_j/s}
=
s\lambda_j,
\]
which proves \eqref{eq:yarn-low-freq-rescaling}. Using \(L'=sL\),
\[
\frac{L'}{\lambda'_j}
=
\frac{sL}{s\lambda_j}
=
\frac{L}{\lambda_j},
\qquad
\Phi(L';\theta'_j)
=
L'\theta'_j
=
sL\frac{\theta_j}{s}
=
L\theta_j
=
\Phi(L;\theta_j).
\]
This proves \eqref{eq:yarn-phase-preservation}.
\end{proof}

\paragraph{Spectral cross-check.}
For each pair \(j\), the complexified matrix \(\mathbf Q(m\theta'_j)\) has eigenvectors \(e_\pm=(1,\mp i)^\top\) with eigenvalues \(e^{\pm i m\theta'_j}\). Since \(|e^{\pm i m\theta'_j}|=1\), the spectral radius is \(1\), and because \(\mathbf Q(m\theta'_j)\) is real orthogonal, its singular values are also \(1\). This independently confirms the isometric/non-expansive conclusion of Proposition~\ref{prop:yarn-operator}; it does not extend that conclusion to a theorem about downstream task accuracy.

Proposition~\ref{prop:yarn-operator} is intentionally operator-level. It establishes that YaRN-scaled RoPE remains orthogonal, preserves RoPE's relative-offset kernel structure, leaves the high-frequency endpoint unchanged, and preserves the pretrained phase budget at the low-frequency endpoint over the extended window. It does not assert monotone improvement of downstream task accuracy, which depends on learned weights, adaptation procedure, data distribution, prompt construction, retrieval position, and decoding.

Performance statements beyond Proposition~\ref{prop:yarn-operator} are therefore empirical. YaRN reports compute-efficient context-window extension with substantially less long-context adaptation than prior approaches in its evaluations, together with strong long-context retrieval behavior, including passkey retrieval at \(128\text{k}\) in its evaluated checkpoints \citep{peng2023yarn}. Qwen2.5-1M further combines long-context model training with an inference framework including length extrapolation, sparse attention, chunked prefill, and serving-level optimizations \citep{yang2025qwen25oneM}. The public Qwen2.5-7B-Instruct-1M model card additionally warns that accuracy may degrade beyond \(262{,}144\) tokens without the specialized long-context framework \citep{qwen2025qwen25oneMcard}.

\paragraph{Hypothesis for AEN.}
Within AEN, the relevant claim is systems-level: if the controller injects relevant curriculum, certification traces, current problem state, and peer critiques while keeping those memories active, safe, and visible, then expanded context should improve runtime reasoning by increasing the amount of useful information that remains simultaneously accessible across the three role sessions before context exhaustion. This is a hypothesis about the full runtime architecture to be evaluated experimentally; it is not a direct corollary of Proposition~\ref{prop:yarn-operator}.
