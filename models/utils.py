def parse_levels(depend_counts, mod_name):
    dep_levels = depend_counts[mod_name]
    if isinstance(dep_levels, int):
        return dep_levels

    levels = []
    for level in dep_levels:
        if isinstance(level, int):
            levels.append(level)
        else:
            parsed_level = parse_levels(depend_counts, level)
            levels.append(parsed_level)
    level = max(levels) + 1
    depend_counts[mod_name] = level
    return level


def get_ordered_tables():
    from models import *
    all_models = [mod for mod in dir()
                  if not mod.startswith('_') and mod not in ('sys')]
    independent_tables = []
    depend_counts = {}
    for mod_name in all_models:
        mod = __import__("models.%s" % mod_name, fromlist=[mod_name])
        depend_tables = mod.foreign_key_tables()
        if not depend_tables:
            independent_tables.append(mod_name)
        else:
            levels = []
            for tbl in depend_tables:
                if tbl in independent_tables:
                    levels.append(1)
                elif isinstance(depend_counts.get(tbl, None), int):
                    levels.append(depend_counts.get(tbl))
                else:
                    levels.append(tbl)
            if all([isinstance(level, int) for level in levels]):
                depend_counts[mod_name] = max(levels)
            else:
                depend_counts[mod_name] = levels
    depend_counts.update({mod_name: 0 for mod_name in independent_tables})
    for mod_name in depend_counts:
        if not isinstance(depend_counts[mod_name], int):
            depend_counts[mod_name] = parse_levels(depend_counts, mod_name)
    return sorted(depend_counts, key=depend_counts.get)


def create_tables():
    all_models = get_ordered_tables()
    print "Tables found to create:", all_models
    for mod_name in all_models:
        __import__("models.%s" % mod_name, fromlist=[mod_name]).create_table()
