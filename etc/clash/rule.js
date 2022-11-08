const test_url = "http://www.gstatic.com/generate_204";
const proxy_groups_key = "proxy-groups";
const interval = 60;
const tolerance = 150;
const proxy_providers_key = "proxy-providers";
const proxies_key = "proxies";
function main(config) {
  if (!(proxy_groups_key in config)) {
    config[proxy_groups_key] = [];
  }
  config[proxy_groups_key] = [
    {
      name: "PROXY",
      type: "select",
      proxies: ["SELECT", "URL-TEST", "FALLBACK", "DIRECT"],
    },
    { name: "SELECT", type: "select", use: [], proxies: [] },
    {
      name: "URL-TEST",
      type: "url-test",
      url: test_url,
      interval: interval,
      tolerance: tolerance,
      use: [],
      proxies: [],
    },
    {
      name: "FALLBACK",
      type: "fallback",
      url: test_url,
      interval: interval,
      use: [],
      proxies: [],
    },
  ];
  config[proxy_groups_key].filter(group => group.name !== 'PROXY').forEach(group => {
    if (proxy_providers_key in config) {
      Object.keys(config[proxy_providers_key]).forEach(provider_name => {
        group.use.push(provider_name);
      });
    }
    if (proxies_key in config) {
      config[proxies_key].forEach(proxy => {
        group.proxies.push(proxy.name);
      });
    }
  });
  return config;
}
