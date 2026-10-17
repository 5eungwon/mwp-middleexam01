package com.example.photoviewer;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import org.json.JSONObject;
import java.util.List;

/** Chapter 5 p.16–17: recycle photo cards as they enter and leave the viewport. */
public final class ImageAdapter extends RecyclerView.Adapter<ImageAdapter.ImageViewHolder> {
    public interface CardFactory { View create(JSONObject post); }
    private final List<JSONObject> posts;
    private final CardFactory factory;

    public ImageAdapter(List<JSONObject> posts, CardFactory factory) {
        this.posts = posts;
        this.factory = factory;
    }
    @NonNull @Override public ImageViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int type) {
        FrameLayout container = (FrameLayout) LayoutInflater.from(parent.getContext())
            .inflate(R.layout.item_image, parent, false);
        return new ImageViewHolder(container);
    }
    @Override public void onBindViewHolder(@NonNull ImageViewHolder holder, int position) {
        holder.container.removeAllViews();
        holder.container.addView(factory.create(posts.get(position)),
            new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
    }
    @Override public int getItemCount() { return posts.size(); }
    public static final class ImageViewHolder extends RecyclerView.ViewHolder {
        final FrameLayout container;
        ImageViewHolder(FrameLayout container) { super(container); this.container = container; }
    }
}
