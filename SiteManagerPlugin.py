import logging
import re
import time

from Config import config
from Plugin import PluginManager

allow_reload = False  # No reload supported

log = logging.getLogger("nametrustPlugin")


@PluginManager.registerTo("SiteManager")
class SiteManagerPlugin(object):
    site_nametrust = None
    db_domains = {}
    db_domains_modified = None

    def load(self, *args, **kwargs):
        super(SiteManagerPlugin, self).load(*args, **kwargs)
        if not self.get(config.trust_resolver):
            self.need(config.trust_resolver)  # Need nametrust site

    # Return: True if the address is .trust domain
    def istrustDomain(self, address):
        return re.match(r"(.*?)([A-Za-z0-9_-]+\.trust)$", address)

    # Resolve domain
    # Return: The address or None
    def resolvetrustDomain(self, domain):
        domain = domain.lower()
        if not self.site_nametrust:
            self.site_nametrust = self.need(config.trust_resolver)

        site_nametrust_modified = self.site_nametrust.content_manager.contents.get("content.json", {}).get("modified", 0)
        if not self.db_domains or self.db_domains_modified != site_nametrust_modified:
            self.site_nametrust.needFile("data/names.json", priority=10)
            s = time.time()
            try:
                self.db_domains = self.site_nametrust.storage.loadJson("data/names.json")
            except Exception as err:
                log.error("Error loading names.json: %s" % err)

            log.debug(
                "Domain db with %s entries loaded in %.3fs (modification: %s -> %s)" %
                (len(self.db_domains), time.time() - s, self.db_domains_modified, site_nametrust_modified)
            )
            self.db_domains_modified = site_nametrust_modified
        return self.db_domains.get(domain)

    # Turn domain into address
    def resolveDomain(self, domain):
        return self.resolvetrustDomain(domain) or super(SiteManagerPlugin, self).resolveDomain(domain)

    # Return: True if the address is domain
    def isDomain(self, address):
        return self.istrustDomain(address) or super(SiteManagerPlugin, self).isDomain(address)


@PluginManager.registerTo("ConfigPlugin")
class ConfigPlugin(object):
    def createArguments(self):
        group = self.parser.add_argument_group("nametrust plugin")
        group.add_argument(
            "--trust_resolver", help="ZeroNet site to resolve .trust domains",
            default="1PtFxzJ8NECkYQzziGWoEfzScD6NiEgqDY", metavar="address"
        )

        return super(ConfigPlugin, self).createArguments()
