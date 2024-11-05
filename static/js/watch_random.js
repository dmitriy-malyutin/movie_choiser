document.addEventListener('DOMContentLoaded', () => {
    console.log("Страница загружена, инициализация скрипта.");

    const nextButton = document.getElementById("nextButton");
    const videoPlayer = document.getElementById("videoPlayer");
    const videoName = document.getElementById("videoName");

    nextButton.addEventListener("click", () => {
        const currentVideoName = videoName.textContent;
        fetch(`/get_next_video?current_video_name=${currentVideoName}`)
            .then(response => response.json())
            .then(data => {
                if (data.video_path) {
                    videoPlayer.src = data.video_path;
                    videoName.textContent = data.video_name;
                    videoPlayer.load();
                    videoPlayer.play();
                } else {
                    alert("Следующая серия не найдена.");
                }
            })
            .catch(error => console.error("Ошибка при загрузке следующей серии:", error));
    });
});
