from src.orchestration.orchestrator import Orchestrator

def main():
    aoi = {
        'type': 'Polygon',
        'coordinates': [[ [78.4, 17.4], [78.5, 17.4], [78.5, 17.5], [78.4, 17.5], [78.4, 17.4] ]]
    }
    o = Orchestrator()
    res = o.run('test_job', aoi, '2023-01-01', '2023-12-01')
    print('Success:', res.success)
    if res.error:
        print('Error:', res.error)

if __name__ == "__main__":
    main()
