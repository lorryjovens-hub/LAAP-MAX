    def find_analogy(self, source_domain: str,
                     target_domain: str = None,
                     source_graph: StructuralGraph = None,
                     target_graph: StructuralGraph = None) -> Optional[AnalogyMapping]:

        """Auto-documented by AGI CodeEvolution.
        Complexity: 11.0. Consider decomposition.
        """
        """
        Find the best analogy between two domains or from one domain to all others.
        """
        src = source_graph or self.domains.get(source_domain)
        if not src:
            logger.warning(f"Unknown source domain: {source_domain}")
            return None

        if target_domain and target_graph:
            tgt = target_graph
        elif target_domain:
            tgt = self.domains.get(target_domain)
            if not tgt:
                # Try to auto-encode from name similarity
                tgt = self._find_domain_by_similarity(target_domain)
                if not tgt:
                    return None
        else:
            # Find best match from all domains
            best = None
            best_score = 0.0
            for dname, dgraph in self.domains.items():
                if dname == source_domain:
                    continue
                mapping = self.aligner.align(src, dgraph)
                if mapping.overall_confidence > best_score:
                    best = mapping
                    best_score = mapping.overall_confidence
            if best:
                self.mappings.append(best)
            return best

        mapping = self.aligner.align(src, tgt)
        self.mappings.append(mapping)
        return mapping
