def get_all_subclasses(cls) -> set[type]:
    subclasses = set(cls.__subclasses__())
    for subclass in cls.__subclasses__():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses
