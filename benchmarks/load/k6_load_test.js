import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 50 },   // Ramp up
        { duration: '1m', target: 200 },   // Steady state
        { duration: '30s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<300'],  // 95% under 300ms
        http_req_failed: ['rate<0.01'],    // <1% errors
    },
};

export default function () {
    const res = http.get('http://127.0.0.1:8080/api/status');
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response valid': (r) => r.json('status') === 'ok',
    });
    sleep(1);
}
