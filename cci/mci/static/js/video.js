function manage_video(domain,
                      display_my_stream_only, 
                      TB,
                      session_id, 
                      token, 
                      sid, 
                      video_width, 
                      video_height) {

    TB.setLogLevel(TB.INFO);
    var apiKey = '21112792';
    
    var session = TB.initSession(session_id);
    session.addEventListener('sessionConnected', handleSessionConnected);
    session.addEventListener('streamCreated',    handleStreamCreated);
    session.addEventListener('streamDestroyed',  handleStreamDestroyed);
    session.connect(apiKey, token);
    
    function handleSessionConnected(event) {
    
        // Subscribe to streams that were in the session when we connected
        subscribeToStreams(event.streams);

        // Publish our own stream (if we're not already doing so in another window) 
        var vid_container = $('#video-container-' + sid);
        if (vid_container.length > 0) {
            var existing_vid = vid_container.children("object[type=application/x-shockwave-flash]");
            if (existing_vid.length == 0) {

                var publisher = TB.initPublisher(apiKey, 'video-' + sid, {
                    name: avatars[sid]['display_name'],
                    width: video_width,
                    height: video_height,
                    publishAudio: false
                });
            
                session.publish(publisher);
                var url = domain + 'mci/published_stream/' + sid + '/';
                console.log(url);
                $.get(url);
            }
        }
    }
    
    function handleStreamCreated(event) {
        subscribeToStreams(event.streams);
    }

    function handleStreamDestroyed(event) {
        for (var i = 0; i < event.streams.length; i++) {
            if (event.streams[i].connection.connectionId != session.connection.connectionId) {
                unbind_stream(event.streams[i]);
            }
        }
    }
    
    function subscribeToStreams(streams) {
        if (!display_my_stream_only) {
            for (var i = 0; i < streams.length; i++) {
                if (streams[i].connection.connectionId != session.connection.connectionId) {
                    var pub_sid = JSON.parse(streams[i].connection.data).sid;
                    bind_stream(streams[i], pub_sid);
                    var url = domain + 'mci/subscribed_to_stream/' + sid + '/' + pub_sid;
                    console.log(url);
                    $.get(url);
                }
            }
        }
    }

    function bind_stream(stream, pub_sid) {
    
        // Display this stream (if it's not already being displayed)
        var vid_container = $('#video-container-' + pub_sid);
        var existing_vid = vid_container.children("object[type=application/x-shockwave-flash]");
        if (existing_vid.length == 0) {
            var div_id = 'video-' + pub_sid;
            session.subscribe(
                stream,
                div_id,
                {
                    width: video_width,
                    height: video_height
                });
            }
    }

    function unbind_stream(stream) {
    
        // Display this stream (if it's not already being displayed)
        var sid = JSON.parse(stream.connection.data).sid;
        var vid_container = $('#video-container-' + sid);
        var existing_vid = vid_container.children("object[type=application/x-shockwave-flash]");
        if (existing_vid.length == 1) {
            var div_id = 'video-' + sid;
            var div = $('<div></div>').attr('id', div_id);
            vid_container.prepend(div);
            existing_vid[0].remove();
        }
    }
}
