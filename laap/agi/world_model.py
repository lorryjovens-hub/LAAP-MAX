    def add_entity(self, name: str, entity_type: EntityType = EntityType.UNKNOWN,
                   properties: Dict[str, Any] = None, tags: Set[str] = None,
                   confidence: float = 0.5, source: str = "observation") -> Entity:

        """Auto-documented by AGI CodeEvolution.
        Complexity: 12.0. Consider decomposition.
        """
        """Add or get an entity in the world model."""
        with self._lock:
            # Check if exists
            existing_id = self._entity_by_name.get(name.lower())
            if existing_id and existing_id in self.entities:
                entity = self.entities[existing_id]
                # Update properties with new information
                if properties:
                    for k, v in properties.items():
                        entity.set(k, v, confidence, source)
                if tags:
                    entity.tags.update(tags)
                    for t in tags:
                        if entity.id not in self._tags_index[t]:
                            self._tags_index[t].append(entity.id)
                entity.touch()
                return entity

            # Create new
            eid = str(uuid.uuid4())[:12]
            entity = Entity(
                id=eid,
                name=name,
                entity_type=entity_type,
                tags=tags or set(),
            )
            if properties:
                for k, v in properties.items():
                    entity.set(k, v, confidence, source)

            if len(self.entities) >= self.max_entities:
                self._evict_least_salient()

            self.entities[eid] = entity
            self._entity_by_name[name.lower()] = eid
            self._entity_by_type[entity_type].append(eid)
            for t in entity.tags:
                self._tags_index[t].append(eid)

            return entity
