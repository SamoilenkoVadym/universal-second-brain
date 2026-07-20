from second_brain.automation import task_map


def test_complete_automation_inventory_is_registered():
    names = task_map()
    for required in ("enrichment", "semantic-index", "obsidian-index", "skills-index", "quality-gate", "dedupe", "watchdog"):
        assert required in names
