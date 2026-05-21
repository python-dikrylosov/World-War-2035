"""
Hybrid Solver Module

Automatically chooses between classical and quantum approaches
based on problem size and complexity.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from .quantum_optimizer import QuantumOptimizer
except ImportError:
    from quantum_optimizer import QuantumOptimizer


@dataclass
class HybridConfig:
    """Configuration for hybrid solver"""
    quantum_backend: str = "qasm_simulator"
    classical_backend: str = "cpu"  # or "gpu"
    auto_switch: bool = True
    problem_size_threshold: int = 20
    time_limit_seconds: float = 60.0


class HybridSolver:
    """
    Hybrid solver that automatically selects the best approach
    (classical or quantum) based on problem characteristics.
    """
    
    def __init__(
        self,
        quantum_backend: str = "qasm_simulator",
        classical_backend: str = "cpu",
        auto_switch: bool = True
    ):
        self.config = HybridConfig(
            quantum_backend=quantum_backend,
            classical_backend=classical_backend,
            auto_switch=auto_switch
        )
        self.quantum_optimizer = QuantumOptimizer(backend=quantum_backend)
        self._stats = {
            "quantum_runs": 0,
            "classical_runs": 0,
            "total_solves": 0
        }
    
    async def solve_optimization(
        self,
        problem: Dict[str, Any],
        objective: Callable[[List[float]], float],
        bounds: List[Tuple[float, float]]
    ) -> Tuple[List[float], float]:
        """
        Solve optimization problem using best available method.
        
        Args:
            problem: Problem description dictionary
            objective: Objective function to minimize
            bounds: Parameter bounds
            
        Returns:
            Tuple of (best_parameters, best_value)
        """
        self._stats["total_solves"] += 1
        
        # Estimate problem size
        problem_size = self._estimate_problem_size(problem, bounds)
        
        # Choose method
        use_quantum = self._should_use_quantum(problem_size)
        
        if use_quantum:
            self._stats["quantum_runs"] += 1
            return await self.solve_quantum(objective, bounds)
        else:
            self._stats["classical_runs"] += 1
            return await self.solve_classical(objective, bounds)
    
    async def solve_quantum(
        self,
        objective: Callable[[List[float]], float],
        bounds: List[Tuple[float, float]]
    ) -> Tuple[List[float], float]:
        """Solve using quantum optimizer"""
        return await self.quantum_optimizer.qaoa_optimize(objective, bounds)
    
    async def solve_classical(
        self,
        objective: Callable[[List[float]], float],
        bounds: List[Tuple[float, float]]
    ) -> Tuple[List[float], float]:
        """Solve using classical optimization"""
        try:
            from scipy.optimize import differential_evolution
            
            result = await asyncio.to_thread(
                differential_evolution,
                objective,
                bounds,
                maxiter=100,
                tol=1e-6
            )
            return result.x.tolist(), float(result.fun)
            
        except ImportError:
            # Fallback to simple optimization
            return await self.quantum_optimizer._qaoa_optimize_classical(
                objective, bounds
            )
    
    def _estimate_problem_size(
        self,
        problem: Dict[str, Any],
        bounds: List[Tuple[float, float]]
    ) -> int:
        """Estimate problem size/complexity"""
        # Number of parameters is a good proxy
        n_params = len(bounds)
        
        # Check for additional complexity indicators
        constraints = problem.get("constraints", {})
        n_constraints = len(constraints) if isinstance(constraints, dict) else 0
        
        # Simple heuristic: params + constraints
        return n_params + n_constraints
    
    def _should_use_quantum(self, problem_size: int) -> bool:
        """Decide whether to use quantum approach"""
        if not self.config.auto_switch:
            return False
        
        # Use quantum for medium-to-large problems
        # (where quantum advantage might appear)
        return problem_size >= self.config.problem_size_threshold
    
    def get_stats(self) -> Dict[str, int]:
        """Get solver statistics"""
        return self._stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "quantum_runs": 0,
            "classical_runs": 0,
            "total_solves": 0
        }


async def demo_hybrid_solver():
    """Demonstration of hybrid solver capabilities"""
    print("=" * 50)
    print("Hybrid Solver Demo")
    print("=" * 50)
    
    solver = HybridSolver(auto_switch=True)
    
    # Example 1: Simple quadratic function
    print("\n1. Minimizing f(x) = x^2")
    
    def objective(params):
        x = params[0]
        return x ** 2
    
    bounds = [(-10, 10)]
    problem = {"type": "quadratic"}
    
    result = await solver.solve_optimization(problem, objective, bounds)
    print(f"   Result: x = {result[0][0]:.6f}, f(x) = {result[1]:.6f}")
    print(f"   Expected: x = 0, f(x) = 0")
    
    # Example 2: Rosenbrock function (harder)
    print("\n2. Minimizing Rosenbrock function")
    
    def rosenbrock(params):
        x, y = params
        return (1 - x)**2 + 100*(y - x**2)**2
    
    bounds = [(-2, 2), (-2, 2)]
    problem = {"type": "rosenbrock"}
    
    result = await solver.solve_optimization(problem, rosenbrock, bounds)
    print(f"   Result: x = {result[0][0]:.6f}, y = {result[0][1]:.6f}")
    print(f"   f(x,y) = {result[1]:.6f}")
    print(f"   Expected: x = 1, y = 1, f(x,y) = 0")
    
    # Show statistics
    print("\n3. Solver Statistics:")
    stats = solver.get_stats()
    print(f"   Total solves: {stats['total_solves']}")
    print(f"   Quantum runs: {stats['quantum_runs']}")
    print(f"   Classical runs: {stats['classical_runs']}")
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(demo_hybrid_solver())
