class ChannelScheduler:
    @staticmethod
    def allocate(table_data: list, total_sites: int, slot_map: dict, channels_per_board: dict) -> list:
        """
        :param table_data: [{"resources": ["ACM200"], ...}, ...]
        :return: 包含分配结果的列表
        """
        usage_counter = {str(s): {res: 0 for res in channels_per_board.keys()} for s in range(1, total_sites + 1)}
        allocations = []
        
        for row_dict in table_data:
            selected_resources = row_dict.get("resources", [])
            row_allocations = [] 
            
            for site_idx in range(1, total_sites + 1):
                site_id = str(site_idx)
                site_str_parts = []
                
                for res in selected_resources:
                    if res in ["GND", "VCC"]: continue
                    
                    boards = slot_map.get(site_id, {}).get(res, [])
                    cap = channels_per_board.get(res, 1)
                    
                    if not boards:
                        raise ValueError(f"Site {site_id} lacks {res} board in Excel!")
                    
                    curr_idx = usage_counter[site_id][res]
                    if curr_idx >= len(boards) * cap:
                        raise ValueError(f"Site {site_id} {res} exhausted!")
                    
                    b_idx = curr_idx // cap
                    c_idx = curr_idx % cap
                    actual_slot = boards[b_idx]
                    
                    site_str_parts.append(f"{res}[S{actual_slot}_CH{c_idx}]")
                    usage_counter[site_id][res] += 1
                
                if site_str_parts:
                    row_allocations.append(f"Site{site_id}({', '.join(site_str_parts)})")
                    
            allocations.append(" | ".join(row_allocations))
            
        return allocations