def includeme(config):
    config.include(".oauth")
    config.include(".diagram_renderer")
    config.include(".diagram_repo")
    config.include(".folder_repo")
    config.include(".organization_repo")
