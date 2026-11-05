import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const transaction = JSON.parse(open(__ENV.TRANSACTION_FILE));
const transactionDuration = new Trend("transaction_duration", true);
const transactionFailed = new Rate("transaction_failed");
const transactions = new Counter("transactions");

const documentRequest = transaction.requests.find(
    (request) => request.resource_type === "Document"
);
const staticRequests = transaction.requests.filter(
    (request) => !["Document", "XHR", "Fetch"].includes(request.resource_type)
);
const dynamicRequests = transaction.requests.filter(
    (request) => ["XHR", "Fetch"].includes(request.resource_type)
);

export const options = {
    discardResponseBodies: true,
    batch: 10,
    batchPerHost: 6,
    scenarios: {
        navigation_load: {
            executor: "constant-vus",
            vus: Number(__ENV.VUS || 10),
            duration: __ENV.DURATION || "30s",
            gracefulStop: __ENV.GRACEFUL_STOP || "180s",
        },
    },
};

function requestParams(resourceType) {
    return {
        redirects: 4,
        timeout: __ENV.RESOURCE_TIMEOUT || "15s",
        tags: { resource_type: resourceType },
    };
}

function responsePassed(response) {
    return check(response, {
        "transaction resource status == 200": (item) => item.status === 200,
    });
}

function runBatch(requests) {
    if (requests.length === 0) {
        return true;
    }
    const specifications = requests.map((request) => ({
        method: "GET",
        url: request.url,
        params: requestParams(request.resource_type),
    }));
    return http.batch(specifications).every(responsePassed);
}

export default function () {
    const started = Date.now();
    let passed = true;

    try {
        if (!documentRequest) {
            passed = false;
            return;
        }

        const documentResponse = http.get(
            documentRequest.url,
            requestParams(documentRequest.resource_type)
        );
        passed = responsePassed(documentResponse);

        // Browsers request CSS, JavaScript, fonts and other static resources
        // concurrently after receiving the document.
        if (passed) {
            passed = runBatch(staticRequests);
        }

        // XHR/Fetch requests represent the data-loading stage after the shell
        // and executable resources have been retrieved.
        if (passed) {
            passed = runBatch(dynamicRequests);
        }
    } catch (_) {
        passed = false;
    } finally {
        transactionDuration.add(Date.now() - started);
        transactionFailed.add(!passed);
        transactions.add(1);
    }

    sleep(1);
}
