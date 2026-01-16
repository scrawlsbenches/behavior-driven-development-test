"""
Main Graph of Thought implementation.
"""

from __future__ import annotations
from typing import TypeVar, Generic, Any, Callable, Iterator
from collections import deque
import heapq
import json
import time

from .core import (
    Thought,
    ThoughtStatus,
    Edge,
    SearchResult,
    SearchContext,
    GraphConfig,
    SearchConfig,
    ThoughtGenerator,
    ThoughtEvaluator,
    GoalPredicate,
    GraphOperations,
    MetricsCollector,
    Logger,
    TracingProvider,
    GraphPersistence,
    ResourceLimiter,
    EventEmitter,
    GraphEvent,
    EventType,
    NodeNotFoundError,
    CycleDetectedError,
    GraphError,
    ResourceExhaustedError,
)
from .core.defaults import (
    FunctionGenerator,
    FunctionEvaluator,
    ConstantEvaluator,
    InMemoryMetricsCollector,
    StructuredLogger,
    NullTracingProvider,
    SimpleResourceLimiter,
    SimpleEventEmitter,
)

T = TypeVar("T")


class GraphOfThought(Generic[T]):
    """
    A directed graph structure for representing and traversing reasoning processes.
    
    This implementation is designed for extensibility:
    - Pluggable generators and evaluators (for LLM integration)
    - Pluggable persistence (for checkpointing and storage)
    - Pluggable observability (metrics, logging, tracing)
    - Pluggable search strategies
    
    Basic usage:
        ```python
        def evaluate(thought: str) -> float:
            return len(thought) / 100.0
        
        def generate(parent: str) -> list[str]:
            return [f"{parent} -> option A", f"{parent} -> option B"]
        
        graph = GraphOfThought[str](
            evaluator=evaluate,
            generator=generate,
        )
        
        root = graph.add_thought("Start")
        result = await graph.beam_search()
        ```
    
    With dependency injection:
        ```python
        graph = GraphOfThought[str](
            config=GraphConfig.from_env(),
            generator=my_llm_generator,
            evaluator=my_llm_evaluator,
            persistence=my_database_persistence,
            metrics=my_prometheus_collector,
            logger=my_structured_logger,
        )
        ```
    """
    
    def __init__(
        self,
        # Core configuration
        config: GraphConfig | None = None,
        
        # Generation and evaluation (required for search)
        generator: ThoughtGenerator[T] | Callable[[T], list[T]] | None = None,
        evaluator: ThoughtEvaluator[T] | Callable[[T], float] | None = None,
        
        # Optional pluggable components
        persistence: GraphPersistence[T] | None = None,
        metrics: MetricsCollector | None = None,
        logger: Logger | None = None,
        tracer: TracingProvider | None = None,
        resource_limiter: ResourceLimiter | None = None,
        event_emitter: EventEmitter[T] | None = None,
        
        # Legacy simple parameters (for backward compatibility)
        max_depth: int | None = None,
        beam_width: int | None = None,
        allow_cycles: bool | None = None,
    ):
        """
        Initialize the Graph of Thought.
        
        Args:
            config: Complete configuration object
            generator: Thought generator (protocol or simple function)
            evaluator: Thought evaluator (protocol or simple function)
            persistence: Optional persistence backend
            metrics: Optional metrics collector
            logger: Optional structured logger
            tracer: Optional distributed tracer
            resource_limiter: Optional resource limiter
            event_emitter: Optional event emitter
            max_depth: Legacy parameter (use config instead)
            beam_width: Legacy parameter (use config instead)
            allow_cycles: Legacy parameter (use config instead)
        """
        # Configuration
        self._config = config or GraphConfig()
        
        # Apply legacy parameters if provided
        if max_depth is not None:
            self._config.limits.max_depth = max_depth
        if beam_width is not None:
            self._config.search.beam_width = beam_width
        if allow_cycles is not None:
            self._config.allow_cycles = allow_cycles
        
        # Wrap simple functions in protocol adapters
        if generator is None:
            self._generator: ThoughtGenerator[T] = FunctionGenerator(lambda x: [])
        elif callable(generator) and not hasattr(generator, 'generate'):
            self._generator = FunctionGenerator(generator)
        else:
            self._generator = generator
        
        if evaluator is None:
            self._evaluator: ThoughtEvaluator[T] = ConstantEvaluator(0.0)
        elif callable(evaluator) and not hasattr(evaluator, 'evaluate'):
            self._evaluator = FunctionEvaluator(evaluator)
        else:
            self._evaluator = evaluator
        
        # Pluggable components (use null implementations if not provided)
        self._persistence = persistence
        self._metrics = metrics or InMemoryMetricsCollector()
        self._logger = logger or StructuredLogger("graph_of_thought")
        self._tracer = tracer or NullTracingProvider()
        self._resource_limiter = resource_limiter or SimpleResourceLimiter()
        self._event_emitter: EventEmitter[T] = event_emitter or SimpleEventEmitter()
        
        # Graph state
        self._thoughts: dict[str, Thought[T]] = {}
        self._adjacency: dict[str, dict[str, Edge]] = {}
        self._reverse_adjacency: dict[str, set[str]] = {}
        self._root_ids: list[str] = []
        
        # Graph metadata
        self._graph_id: str | None = None
        self._created_at: float = time.time()
        self._metadata: dict[str, Any] = {}
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def config(self) -> GraphConfig:
        """Get the graph configuration."""
        return self._config
    
    @property
    def thoughts(self) -> dict[str, Thought[T]]:
        """Read-only access to thoughts dictionary."""
        return dict(self._thoughts)
    
    @property
    def root_ids(self) -> list[str]:
        """Read-only access to root IDs."""
        return list(self._root_ids)
    
    @property
    def edges(self) -> list[Edge]:
        """Get all edges in the graph."""
        return [
            edge 
            for targets in self._adjacency.values() 
            for edge in targets.values()
        ]
    
    # =========================================================================
    # Basic Operations
    # =========================================================================
    
    def __contains__(self, thought_id: str) -> bool:
        return thought_id in self._thoughts
    
    def __len__(self) -> int:
        return len(self._thoughts)
    
    def __repr__(self) -> str:
        return f"GraphOfThought(thoughts={len(self._thoughts)}, edges={len(self.edges)})"
    
    def _validate_thought_exists(self, thought_id: str) -> None:
        if thought_id not in self._thoughts:
            raise NodeNotFoundError(thought_id)
    
    def _would_create_cycle(self, source_id: str, target_id: str) -> bool:
        if source_id == target_id:
            return True
        
        visited = set()
        queue = deque([target_id])
        
        while queue:
            current = queue.popleft()
            if current == source_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._adjacency.get(current, {}).keys())
        
        return False
    
    # =========================================================================
    # Thought Management
    # =========================================================================
    
    def add_thought(
        self,
        content: T,
        parent_id: str | None = None,
        relation: str = "leads_to",
        weight: float = 1.0,
        score: float | None = None,
        thought_id: str | None = None,
        tokens_used: int = 0,
        generation_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> Thought[T]:
        """
        Add a new thought to the graph.
        
        Args:
            content: The thought content
            parent_id: ID of parent thought (None for root)
            relation: Relationship type to parent
            weight: Edge weight to parent
            score: Pre-computed score (will be computed if None)
            thought_id: Optional specific ID (auto-generated if None)
            tokens_used: Tokens used in generation
            generation_time_ms: Time taken to generate
            metadata: Additional metadata
            
        Returns:
            The created Thought node
        """
        # Check resource limits
        if len(self._thoughts) >= self._config.limits.max_thoughts:
            raise ResourceExhaustedError("thoughts", self._config.limits.max_thoughts)
        
        if parent_id is not None:
            self._validate_thought_exists(parent_id)
            parent_depth = self._thoughts[parent_id].depth
        else:
            parent_depth = -1
        
        import uuid
        thought = Thought(
            content=content,
            score=score if score is not None else 0.0,
            depth=parent_depth + 1,
            id=thought_id or uuid.uuid4().hex,
            tokens_used=tokens_used,
            generation_time_ms=generation_time_ms,
            metadata=metadata or {},
        )
        
        if thought.id in self._thoughts:
            raise GraphError(f"Thought ID '{thought.id}' already exists")
        
        self._thoughts[thought.id] = thought
        self._adjacency[thought.id] = {}
        self._reverse_adjacency[thought.id] = set()
        
        if parent_id is None:
            self._root_ids.append(thought.id)
        else:
            self._add_edge(parent_id, thought.id, relation, weight)
        
        # Metrics
        self._metrics.increment("thoughts.added")
        self._metrics.gauge("thoughts.total", len(self._thoughts))
        
        # Emit event
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._event_emitter.emit(
                GraphEvent(EventType.THOUGHT_ADDED, thought=thought)
            ))
        except RuntimeError:
            pass  # No event loop running
        
        return thought
    
    async def add_thought_async(
        self,
        content: T,
        parent_id: str | None = None,
        relation: str = "leads_to",
        weight: float = 1.0,
        score: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Thought[T]:
        """Async version of add_thought that evaluates score if not provided."""
        if score is None:
            context = self._make_context(parent_id)
            start_time = time.time()
            score = await self._evaluator.evaluate(content, context)
            eval_time = (time.time() - start_time) * 1000
            self._metrics.timing("thought.evaluation_ms", eval_time)
        
        return self.add_thought(
            content, parent_id, relation, weight, score, metadata=metadata
        )
    
    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str = "leads_to",
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> Edge:
        self._validate_thought_exists(source_id)
        self._validate_thought_exists(target_id)
        
        if not self._config.allow_cycles and self._would_create_cycle(source_id, target_id):
            raise CycleDetectedError(source_id, target_id)
        
        edge = Edge(source_id, target_id, relation, weight, metadata or {})
        self._adjacency[source_id][target_id] = edge
        self._reverse_adjacency[target_id].add(source_id)
        
        self._metrics.increment("edges.added")
        
        return edge
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str = "leads_to",
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> Edge:
        """Public method to add an edge between existing thoughts."""
        return self._add_edge(source_id, target_id, relation, weight, metadata)
    
    def remove_thought(self, thought_id: str) -> Thought[T]:
        """Remove a thought and all its connected edges."""
        self._validate_thought_exists(thought_id)
        
        thought = self._thoughts.pop(thought_id)
        
        if thought_id in self._root_ids:
            self._root_ids.remove(thought_id)
        
        del self._adjacency[thought_id]
        
        for parent_id in self._reverse_adjacency.pop(thought_id, set()):
            if parent_id in self._adjacency:
                self._adjacency[parent_id].pop(thought_id, None)
        
        for targets in self._adjacency.values():
            targets.pop(thought_id, None)
        
        for sources in self._reverse_adjacency.values():
            sources.discard(thought_id)
        
        self._metrics.increment("thoughts.removed")
        self._metrics.gauge("thoughts.total", len(self._thoughts))
        
        return thought
    
    def remove_edge(self, source_id: str, target_id: str) -> Edge | None:
        """Remove an edge between two thoughts."""
        edge = self._adjacency.get(source_id, {}).pop(target_id, None)
        if edge:
            self._reverse_adjacency.get(target_id, set()).discard(source_id)
            self._metrics.increment("edges.removed")
        return edge
    
    # =========================================================================
    # Graph Queries
    # =========================================================================
    
    def get_thought(self, thought_id: str) -> Thought[T]:
        """Get a thought by ID."""
        self._validate_thought_exists(thought_id)
        return self._thoughts[thought_id]
    
    def get_children(self, thought_id: str) -> list[Thought[T]]:
        """Get all child thoughts."""
        self._validate_thought_exists(thought_id)
        return [
            self._thoughts[cid] 
            for cid in self._adjacency.get(thought_id, {}).keys()
        ]
    
    def get_parents(self, thought_id: str) -> list[Thought[T]]:
        """Get all parent thoughts."""
        self._validate_thought_exists(thought_id)
        return [
            self._thoughts[pid] 
            for pid in self._reverse_adjacency.get(thought_id, set())
        ]
    
    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        """Get the edge between two thoughts."""
        return self._adjacency.get(source_id, {}).get(target_id)
    
    def get_path_to_root(self, thought_id: str) -> list[Thought[T]]:
        """Get a path from a thought to a root."""
        self._validate_thought_exists(thought_id)
        
        path = []
        current_id: str | None = thought_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            path.append(self._thoughts[current_id])
            parents = self._reverse_adjacency.get(current_id, set())
            current_id = next(iter(parents), None)
        
        return list(reversed(path))
    
    def get_leaves(self, include_pruned: bool = False) -> list[Thought[T]]:
        """Get all leaf thoughts (no children)."""
        return [
            thought for tid, thought in self._thoughts.items()
            if not self._adjacency.get(tid)
            and (include_pruned or thought.status != ThoughtStatus.PRUNED)
        ]
    
    def get_best_path(self) -> list[Thought[T]]:
        """Get the path to the highest-scoring leaf."""
        leaves = self.get_leaves()
        if not leaves:
            return []
        best_leaf = max(leaves, key=lambda t: t.score)
        return self.get_path_to_root(best_leaf.id)
    
    # =========================================================================
    # Traversal
    # =========================================================================
    
    def bfs(
        self, 
        start_id: str | None = None,
        include_pruned: bool = False,
    ) -> Iterator[Thought[T]]:
        """Breadth-first traversal."""
        if start_id:
            self._validate_thought_exists(start_id)
            start_ids = [start_id]
        else:
            start_ids = self._root_ids
        
        visited: set[str] = set()
        queue = deque(start_ids)
        
        while queue:
            current_id = queue.popleft()
            if current_id in visited:
                continue
            
            visited.add(current_id)
            thought = self._thoughts[current_id]
            
            if include_pruned or thought.status != ThoughtStatus.PRUNED:
                yield thought
            
            for child_id in self._adjacency.get(current_id, {}).keys():
                if child_id not in visited:
                    queue.append(child_id)
    
    def dfs(
        self, 
        start_id: str | None = None,
        include_pruned: bool = False,
    ) -> Iterator[Thought[T]]:
        """Depth-first traversal."""
        if start_id:
            self._validate_thought_exists(start_id)
            start_ids = [start_id]
        else:
            start_ids = self._root_ids
        
        visited: set[str] = set()
        stack = list(reversed(start_ids))
        
        while stack:
            current_id = stack.pop()
            if current_id in visited:
                continue
            
            visited.add(current_id)
            thought = self._thoughts[current_id]
            
            if include_pruned or thought.status != ThoughtStatus.PRUNED:
                yield thought
            
            children = list(self._adjacency.get(current_id, {}).keys())
            for child_id in reversed(children):
                if child_id not in visited:
                    stack.append(child_id)
    
    # =========================================================================
    # Search Operations
    # =========================================================================
    
    def _make_context(
        self,
        thought_id: str | None,
        tokens_remaining: int | None = None,
        time_remaining: float | None = None,
    ) -> SearchContext[T]:
        """Create a search context for a thought."""
        if thought_id is None:
            # Context for root creation
            return SearchContext(
                current_thought=Thought(content=None, depth=-1),  # type: ignore
                path_to_root=[],
                depth=0,
                tokens_remaining=tokens_remaining,
                time_remaining_seconds=time_remaining,
            )
        
        thought = self._thoughts[thought_id]
        path = self.get_path_to_root(thought_id)
        
        return SearchContext(
            current_thought=thought,
            path_to_root=path,
            depth=thought.depth,
            tokens_remaining=tokens_remaining,
            time_remaining_seconds=time_remaining,
        )
    
    async def expand(self, thought_id: str) -> list[Thought[T]]:
        """
        Expand a thought by generating and adding child thoughts.
        
        Uses the configured generator and evaluator.
        """
        self._validate_thought_exists(thought_id)
        thought = self._thoughts[thought_id]
        
        if thought.depth >= self._config.limits.max_depth:
            self._logger.debug("Max depth reached", thought_id=thought_id)
            return []
        
        if thought.status == ThoughtStatus.PRUNED:
            return []
        
        with self._tracer.start_span("expand_thought", attributes={"thought_id": thought_id}):
            thought.status = ThoughtStatus.ACTIVE
            
            context = self._make_context(thought_id)
            
            # Generate children
            start_time = time.time()
            child_contents = await self._generator.generate(thought.content, context)
            gen_time = (time.time() - start_time) * 1000
            self._metrics.timing("thought.generation_ms", gen_time)
            
            children = []
            for content in child_contents:
                # Evaluate each child
                eval_start = time.time()
                score = await self._evaluator.evaluate(content, context)
                eval_time = (time.time() - eval_start) * 1000
                
                child = self.add_thought(
                    content,
                    parent_id=thought_id,
                    score=score,
                    generation_time_ms=eval_time,
                )
                children.append(child)
            
            thought.status = ThoughtStatus.COMPLETED
            
            self._metrics.increment("thoughts.expanded")
            self._metrics.histogram("expansion.children_count", len(children))
            
            await self._event_emitter.emit(
                GraphEvent(EventType.THOUGHT_EXPANDED, thought=thought, metadata={"children": len(children)})
            )
        
        return children
    
    async def beam_search(
        self,
        start_id: str | None = None,
        goal: GoalPredicate[T] | Callable[[T], bool] | None = None,
        config: SearchConfig | None = None,
    ) -> SearchResult[T]:
        """
        Perform beam search to find the best reasoning path.
        
        Args:
            start_id: Starting thought ID (uses roots if None)
            goal: Optional goal predicate for early termination
            config: Search configuration (uses defaults if None)
            
        Returns:
            SearchResult with best path and statistics
        """
        cfg = config or SearchConfig(
            max_depth=self._config.limits.max_depth,
            beam_width=self._config.search.beam_width,
            max_expansions=self._config.search.max_expansions,
            max_tokens=self._config.limits.max_tokens,
            timeout_seconds=self._config.limits.timeout_seconds,
        )
        
        start_time = time.time()
        total_tokens = 0
        expansions = 0
        termination_reason = "completed"
        
        with self._tracer.start_span("beam_search"):
            await self._event_emitter.emit(
                GraphEvent(EventType.SEARCH_STARTED, metadata={"strategy": "beam_search"})
            )
            
            if start_id:
                self._validate_thought_exists(start_id)
                current_beam = [self._thoughts[start_id]]
            else:
                current_beam = [self._thoughts[rid] for rid in self._root_ids]
            
            if not current_beam:
                return SearchResult(
                    best_path=[],
                    best_score=0.0,
                    thoughts_explored=0,
                    thoughts_expanded=0,
                    total_tokens_used=0,
                    wall_time_seconds=0.0,
                    termination_reason="no_roots",
                )
            
            best_thought = max(current_beam, key=lambda t: t.score)
            expanded: set[str] = set()
            
            while current_beam:
                # Check timeout
                elapsed = time.time() - start_time
                if cfg.timeout_seconds and elapsed >= cfg.timeout_seconds:
                    termination_reason = "timeout"
                    break
                
                # Check goal
                if goal:
                    for thought in current_beam:
                        if (callable(goal) and goal(thought.content)):
                            termination_reason = "goal_reached"
                            best_thought = thought
                            await self._event_emitter.emit(
                                GraphEvent(EventType.GOAL_REACHED, thought=thought)
                            )
                            break
                    if termination_reason == "goal_reached":
                        break
                
                # Check expansion limit
                if expansions >= cfg.max_expansions:
                    termination_reason = "max_expansions"
                    break
                
                # Expand beam
                all_children: list[Thought[T]] = []
                for thought in current_beam:
                    if thought.id in expanded:
                        continue
                    if thought.depth >= cfg.max_depth:
                        continue
                    if thought.status == ThoughtStatus.PRUNED:
                        continue
                    
                    children = await self.expand(thought.id)
                    all_children.extend(children)
                    expanded.add(thought.id)
                    expansions += 1
                    
                    for child in children:
                        total_tokens += child.tokens_used
                        if child.score > best_thought.score:
                            best_thought = child
                    
                    # Check token budget
                    if cfg.max_tokens and total_tokens >= cfg.max_tokens:
                        termination_reason = "budget_exhausted"
                        break
                
                if termination_reason != "completed":
                    break
                
                if not all_children:
                    break
                
                all_children.sort(key=lambda t: t.score, reverse=True)
                current_beam = all_children[:cfg.beam_width]
            
            wall_time = time.time() - start_time
            best_path = self.get_path_to_root(best_thought.id)
            
            self._metrics.timing("search.beam_search_ms", wall_time * 1000)
            self._metrics.histogram("search.expansions", expansions)
            
            result = SearchResult(
                best_path=best_path,
                best_score=best_thought.score,
                thoughts_explored=len(self._thoughts),
                thoughts_expanded=expansions,
                total_tokens_used=total_tokens,
                wall_time_seconds=wall_time,
                termination_reason=termination_reason,
            )
            
            await self._event_emitter.emit(
                GraphEvent(EventType.SEARCH_COMPLETED, metadata={"result": termination_reason})
            )
            
            return result
    
    async def best_first_search(
        self,
        start_id: str | None = None,
        goal: GoalPredicate[T] | Callable[[T], bool] | None = None,
        config: SearchConfig | None = None,
    ) -> SearchResult[T]:
        """
        Perform best-first search using thought scores as priority.
        """
        cfg = config or SearchConfig(
            max_depth=self._config.limits.max_depth,
            max_expansions=self._config.search.max_expansions,
            max_tokens=self._config.limits.max_tokens,
            timeout_seconds=self._config.limits.timeout_seconds,
        )
        
        start_time = time.time()
        total_tokens = 0
        expansions = 0
        termination_reason = "completed"
        
        with self._tracer.start_span("best_first_search"):
            if start_id:
                self._validate_thought_exists(start_id)
                initial = [self._thoughts[start_id]]
            else:
                initial = [self._thoughts[rid] for rid in self._root_ids]
            
            if not initial:
                return SearchResult(
                    best_path=[],
                    best_score=0.0,
                    thoughts_explored=0,
                    thoughts_expanded=0,
                    total_tokens_used=0,
                    wall_time_seconds=0.0,
                    termination_reason="no_roots",
                )
            
            heap = list(initial)
            heapq.heapify(heap)
            
            expanded: set[str] = set()
            best_thought: Thought[T] | None = None
            
            while heap and expansions < cfg.max_expansions:
                # Check timeout
                elapsed = time.time() - start_time
                if cfg.timeout_seconds and elapsed >= cfg.timeout_seconds:
                    termination_reason = "timeout"
                    break
                
                current = heapq.heappop(heap)
                
                if current.id in expanded:
                    continue
                
                if best_thought is None or current.score > best_thought.score:
                    best_thought = current
                
                if goal and callable(goal) and goal(current.content):
                    termination_reason = "goal_reached"
                    best_thought = current
                    break
                
                if current.status == ThoughtStatus.PRUNED:
                    continue
                
                expanded.add(current.id)
                children = await self.expand(current.id)
                
                for child in children:
                    total_tokens += child.tokens_used
                    if child.id not in expanded:
                        heapq.heappush(heap, child)
                
                expansions += 1
                
                if cfg.max_tokens and total_tokens >= cfg.max_tokens:
                    termination_reason = "budget_exhausted"
                    break
            
            wall_time = time.time() - start_time
            best_path = self.get_path_to_root(best_thought.id) if best_thought else []
            
            return SearchResult(
                best_path=best_path,
                best_score=best_thought.score if best_thought else 0.0,
                thoughts_explored=len(self._thoughts),
                thoughts_expanded=expansions,
                total_tokens_used=total_tokens,
                wall_time_seconds=wall_time,
                termination_reason=termination_reason,
            )
    
    # =========================================================================
    # Merge and Prune
    # =========================================================================
    
    def merge_thoughts(
        self,
        thought_ids: list[str],
        merged_content: T,
        relation: str = "merges_into",
        weight: float = 1.0,
        score: float | None = None,
    ) -> Thought[T]:
        """Merge multiple thoughts into a new synthesized thought."""
        if not thought_ids:
            raise GraphError("Cannot merge empty list of thoughts")
        
        for tid in thought_ids:
            self._validate_thought_exists(tid)
        
        max_depth = max(self._thoughts[tid].depth for tid in thought_ids)
        
        import uuid
        merged = Thought(
            content=merged_content,
            score=score or 0.0,
            depth=max_depth + 1,
            id=uuid.uuid4().hex,
        )
        
        self._thoughts[merged.id] = merged
        self._adjacency[merged.id] = {}
        self._reverse_adjacency[merged.id] = set()
        
        for tid in thought_ids:
            self._add_edge(tid, merged.id, relation, weight)
            self._thoughts[tid].status = ThoughtStatus.MERGED
        
        self._metrics.increment("thoughts.merged")
        
        return merged
    
    def prune(self, threshold: float) -> int:
        """Mark thoughts below threshold as pruned."""
        pruned_count = 0
        for thought in self._thoughts.values():
            if thought.score < threshold and thought.status == ThoughtStatus.PENDING:
                thought.status = ThoughtStatus.PRUNED
                pruned_count += 1
        
        self._metrics.increment("thoughts.pruned", pruned_count)
        return pruned_count
    
    def prune_and_remove(self, threshold: float) -> int:
        """Remove thoughts below threshold from graph."""
        to_remove = [
            tid for tid, thought in self._thoughts.items()
            if thought.score < threshold and thought.status == ThoughtStatus.PENDING
        ]
        
        for tid in to_remove:
            self.remove_thought(tid)
        
        return len(to_remove)
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a dictionary."""
        return {
            "thoughts": {tid: t.to_dict() for tid, t in self._thoughts.items()},
            "edges": [e.to_dict() for e in self.edges],
            "roots": self._root_ids.copy(),
            "config": self._config.to_dict(),
            "metadata": self._metadata,
        }
    
    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        generator: ThoughtGenerator[T] | Callable[[T], list[T]] | None = None,
        evaluator: ThoughtEvaluator[T] | Callable[[T], float] | None = None,
        **kwargs: Any,
    ) -> GraphOfThought[T]:
        """Deserialize a graph from a dictionary."""
        config = GraphConfig.from_dict(data.get("config", {}))
        
        graph: GraphOfThought[T] = cls(
            config=config,
            generator=generator,
            evaluator=evaluator,
            **kwargs,
        )
        
        # Add thoughts
        for tid, thought_data in data["thoughts"].items():
            thought = Thought.from_dict(thought_data)
            graph._thoughts[thought.id] = thought
            graph._adjacency[thought.id] = {}
            graph._reverse_adjacency[thought.id] = set()
        
        graph._root_ids = data.get("roots", [])
        
        # Add edges
        original_allow_cycles = graph._config.allow_cycles
        graph._config.allow_cycles = True
        for edge_data in data["edges"]:
            edge = Edge.from_dict(edge_data)
            if edge.source_id in graph._thoughts and edge.target_id in graph._thoughts:
                graph._adjacency[edge.source_id][edge.target_id] = edge
                graph._reverse_adjacency[edge.target_id].add(edge.source_id)
        graph._config.allow_cycles = original_allow_cycles
        
        graph._metadata = data.get("metadata", {})
        
        return graph
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize the graph to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_json(
        cls,
        json_str: str,
        generator: ThoughtGenerator[T] | Callable[[T], list[T]] | None = None,
        evaluator: ThoughtEvaluator[T] | Callable[[T], float] | None = None,
        **kwargs: Any,
    ) -> GraphOfThought[T]:
        """Deserialize a graph from JSON string."""
        return cls.from_dict(json.loads(json_str), generator, evaluator, **kwargs)
    
    # =========================================================================
    # Visualization
    # =========================================================================
    
    def visualize(self, max_content_length: int = 50) -> str:
        """Generate a text visualization of the graph."""
        lines = ["Graph of Thought", "=" * 40]
        visited_in_tree: set[str] = set()
        
        def render_thought(
            thought_id: str, 
            prefix: str = "", 
            is_last: bool = True,
            ancestors: set[str] | None = None,
        ):
            if ancestors is None:
                ancestors = set()
            
            thought = self._thoughts[thought_id]
            connector = "└── " if is_last else "├── "
            status_icon = {
                ThoughtStatus.PENDING: "○",
                ThoughtStatus.ACTIVE: "●",
                ThoughtStatus.COMPLETED: "✓",
                ThoughtStatus.PRUNED: "✗",
                ThoughtStatus.MERGED: "⊕",
                ThoughtStatus.FAILED: "✖",
            }.get(thought.status, "?")
            
            content_str = str(thought.content)[:max_content_length]
            if len(str(thought.content)) > max_content_length:
                content_str += "..."
            
            if thought_id in ancestors:
                lines.append(f"{prefix}{connector}{status_icon} [{thought.score:.2f}] {content_str} [CYCLE]")
                return
            
            if thought_id in visited_in_tree:
                lines.append(f"{prefix}{connector}{status_icon} [{thought.score:.2f}] {content_str} [→ see above]")
                return
            
            visited_in_tree.add(thought_id)
            lines.append(f"{prefix}{connector}{status_icon} [{thought.score:.2f}] {content_str}")
            
            children = list(self._adjacency.get(thought_id, {}).keys())
            child_prefix = prefix + ("    " if is_last else "│   ")
            new_ancestors = ancestors | {thought_id}
            
            for i, child_id in enumerate(children):
                render_thought(child_id, child_prefix, i == len(children) - 1, new_ancestors)
        
        for i, root_id in enumerate(self._root_ids):
            if i > 0:
                lines.append("")
            render_thought(root_id, "", i == len(self._root_ids) - 1)
        
        disconnected = set(self._thoughts.keys()) - visited_in_tree
        if disconnected:
            lines.append("")
            lines.append("Disconnected thoughts:")
            for tid in disconnected:
                thought = self._thoughts[tid]
                content_str = str(thought.content)[:max_content_length]
                lines.append(f"  ○ [{thought.score:.2f}] {content_str}")
        
        return "\n".join(lines)
    
    def stats(self) -> dict[str, Any]:
        """Get statistics about the graph."""
        status_counts: dict[str, int] = {}
        for thought in self._thoughts.values():
            status_counts[thought.status.name] = status_counts.get(thought.status.name, 0) + 1
        
        depths = [t.depth for t in self._thoughts.values()]
        scores = [t.score for t in self._thoughts.values()]
        
        return {
            "total_thoughts": len(self._thoughts),
            "total_edges": len(self.edges),
            "root_count": len(self._root_ids),
            "leaf_count": len(self.get_leaves()),
            "max_depth": max(depths) if depths else 0,
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "status_counts": status_counts,
        }
    
    # =========================================================================
    # GraphOperations Protocol Implementation
    # =========================================================================
    
    def as_operations(self) -> GraphOperations[T]:
        """
        Return this graph as a GraphOperations interface.
        
        Useful for passing to search strategies.
        """
        return self  # type: ignore
    
    def thought_count(self) -> int:
        """Get total thought count (for GraphOperations protocol)."""
        return len(self._thoughts)
    
    def get_root_ids(self) -> list[str]:
        """Get root IDs (for GraphOperations protocol)."""
        return list(self._root_ids)
    
    def update_thought_status(self, thought_id: str, status: str) -> None:
        """Update thought status (for GraphOperations protocol)."""
        self._validate_thought_exists(thought_id)
        self._thoughts[thought_id].status = ThoughtStatus[status]
