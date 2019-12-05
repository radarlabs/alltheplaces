const dataStr = `
  {
    "spiders": {
        "24_hour_fitness": {"metadata":
            {
                "_shub_worker": "kumo",
                "api_url": "https://dash.scrapinghub.com/api/",
                "deploy_id": 2,
                "priority": 2,
                "tags": [],
                "units": 1,
                "spider_type": "manual",
                "finished_time": 1575572546260,
                "spider": "24_hour_fitness",
                "version": "916c8f4-master",
                "completed_by": "jobrunner",
                "scheduled_by": "blackmad-radar",
                "state": "finished",
                "close_reason": "finished",
                "pending_time": 1575572505413,
                "started_by": "jobrunner",
                "running_time": 1575572505445,
                "scrapystats": {
                    "crawlera/request": 1,
                    "crawlera/request/method/GET": 1,
                    "crawlera/response": 1,
                    "crawlera/response/status/200": 1,
                    "downloader/request_bytes": 552,
                    "downloader/request_count": 1,
                    "downloader/request_method_count/GET": 1,
                    "downloader/response_bytes": 219002,
                    "downloader/response_count": 1,
                    "downloader/response_status_count/200": 1,
                    "finish_reason": "finished",
                    "finish_time": 1575572522846.0,
                    "item_scraped_count": 448,
                    "log_count/INFO": 10,
                    "memusage/max": 62251008,
                    "memusage/startup": 62251008,
                    "response_received_count": 1,
                    "scheduler/dequeued": 1,
                    "scheduler/dequeued/disk": 1,
                    "scheduler/enqueued": 1,
                    "scheduler/enqueued/disk": 1,
                    "start_time": 1575572521167.0
                },
                "project": 419917
            }
          }
    }
}`;

$(document).ready(function() {
  $.ajax({
    url:
      "https://s3.amazonaws.com/com.radar.public.alltheplaces/latest-metadata.json"
  }).done(parseMetadata)
})

function parseMetadata(data) {
  console.log(data)
  // const data = LosslessJSON.parse(dataStr);
  // const data = JSON.parse(dataStr);
  const rows = Object.values(data.spiders);
  rows.forEach((r) =>{
    if (!r.metadata.scrapystats) {
      r.metadata.scrapystats = {}
    }
  })
  $("#example").DataTable({
    // "ajax": "data/objects.txt",
    data: rows,
    paging: false,
    columns: [
      {
        data: "metadata.spider",
        render: d => {
          return `<a href="/${d}/latest.geojson">${d}</a>`;
        }
      },
      { data: "metadata.scrapystats.item_scraped_count", defaultContent: "" },
      {
        data: "metadata.scrapystats.start_time",
        defaultContent: 0,
        render: d => {
          return $.fn.dataTable.render.moment("Do MMM YYYY")(new Date(d));
        }
      }
    ],
    columnDefs: [
      {
        render: function(data, type, row) {
          return new Date(data);
        },
        targets: 2
      }
    ],
    rowCallback: function(row, data, index) {
      console.log(data);
      if (!data.metadata || data.metadata.scrapystats.item_scraped_count == 0) {
        $(row).css("background-color", "lightred");
      }
    }
  });
}
