<!-- ai-generated: 80% - AI documented the measured Toxiproxy experiment and its client/server latency difference -->
# Client-server latency gap

This measurement used Toxiproxy 2.12.0 with a downstream `latency` toxic set to 100 ms latency, 10 ms jitter,
and toxicity 1.0. Toxiproxy listened on port 8666 and forwarded to `svcdesk:8080`. The `itsmlab.ps1 load 3`
60-second open-loop run through `http://host.docker.internal:8666` reported a client p99 of 0.2643 seconds and
the server histogram's p99 over that same run as 0.1586 seconds. The recorded gap is their difference:
0.2643 - 0.1586 = 0.1057 seconds.

The client observes the time from scheduling a request until receiving its response. The server histogram only
times requests inside the service, so its p99 does not include the full network path between the load generator and
the service. The Toxiproxy toxic deliberately adds delay to the downstream response path; jitter varies that
delay. Consequently, the client p99 is higher than the server-side histogram p99. These values describe one
measurement, one toxic configuration, and the profile associated with the configured `kb-index` login; repeat
the load to assess variability rather than treating this single result as a permanent network constant.

## Reproducing the measurement on Windows

From the repository root, start the service, index and optional proxy:

```powershell
docker compose --profile gap up -d --build svcdesk kb-index toxiproxy
```

Create the Toxiproxy proxy and downstream toxic through its API. If repeating a setup that already has a proxy
named `svcdesk`, delete that proxy first with `curl.exe --noproxy '*' -X DELETE
http://127.0.0.1:8474/proxies/svcdesk`.

```powershell
$proxy = '{"name":"svcdesk","listen":"0.0.0.0:8666","upstream":"svcdesk:8080","enabled":true}'
curl.exe --noproxy '*' -X POST http://127.0.0.1:8474/proxies `
  -H 'Content-Type: application/json' --data-binary $proxy
$toxic = '{"name":"downstream-latency","type":"latency","stream":"downstream","toxicity":1.0,"attributes":{"latency":100,"jitter":10}}'
curl.exe --noproxy '*' -X POST http://127.0.0.1:8474/proxies/svcdesk/toxics `
  -H 'Content-Type: application/json' --data-binary $toxic
```

Then run the load through the published proxy port:

```powershell
.\itsmlab.ps1 load 3 --base-url http://host.docker.internal:8666
```

Record the load output's client `q (p99)` and `your histogram's own p99 over the run`, both converted from
milliseconds to seconds. Set `gap_seconds` to client p99 minus server p99. Keep the toxic values identical to
those actually used; the checker independently remeasures the gap with the declared toxic.
