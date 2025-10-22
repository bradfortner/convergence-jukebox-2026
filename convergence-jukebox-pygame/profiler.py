"""
Performance Profiler - Profile application performance and memory usage
"""

import cProfile
import pstats
import io
import time
import tracemalloc
import pygame
from main import JukeboxApplication


class PerformanceProfiler:
    """Profile application performance"""

    def __init__(self):
        """Initialize profiler"""
        self.profiler = cProfile.Profile()
        self.memory_snapshots = []

    def profile_initialization(self):
        """Profile application initialization"""
        print("Profiling initialization...")

        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()

        # Profile app creation
        self.profiler.enable()
        app = JukeboxApplication()
        self.profiler.disable()

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        elapsed_time = time.time() - start_time

        print(f"Initialization time: {elapsed_time:.2f}s")
        print(f"Current memory: {current / 1024 / 1024:.2f}MB")
        print(f"Peak memory: {peak / 1024 / 1024:.2f}MB")

        tracemalloc.stop()

        return app

    def print_stats(self, sort_by='cumulative', top_n=20):
        """Print profiling statistics"""
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(sort_by)
        ps.print_stats(top_n)
        print(s.getvalue())

    def profile_operation(self, operation_name, operation_func):
        """Profile a specific operation"""
        print(f"\nProfiling {operation_name}...")

        tracemalloc.start()
        start_time = time.time()

        # Run operation
        try:
            operation_func()
        except Exception as e:
            print(f"Error during operation: {e}")

        elapsed_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()

        print(f"Operation time: {elapsed_time:.3f}s")
        print(f"Memory used: {(peak - current) / 1024:.2f}KB")

        tracemalloc.stop()

        return elapsed_time

    @staticmethod
    def profile_rendering_fps(duration=10):
        """Profile rendering FPS"""
        print(f"\nProfiling FPS for {duration} seconds...")

        pygame.init()
        from ui_engine import UIEngine
        import config

        ui_engine = UIEngine()
        frame_count = 0
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                ui_engine.fill(config.COLOR_BLACK)
                ui_engine.update_display()
                ui_engine.get_frame_rate()
                frame_count += 1
        except KeyboardInterrupt:
            pass

        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0

        print(f"Frames rendered: {frame_count}")
        print(f"Average FPS: {avg_fps:.1f}")

        ui_engine.quit()


def run_full_profile():
    """Run full application profile"""
    print("="*70)
    print("CONVERGENCE JUKEBOX - PERFORMANCE PROFILE")
    print("="*70)

    profiler = PerformanceProfiler()

    # Profile initialization
    try:
        app = profiler.profile_initialization()
        profiler.print_stats(top_n=10)

        # Profile FPS
        try:
            profiler.profile_rendering_fps(duration=5)
        except Exception as e:
            print(f"Could not profile FPS: {e}")

    except Exception as e:
        print(f"Profiling error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print("Profile complete")
    print("="*70)


if __name__ == '__main__':
    run_full_profile()
