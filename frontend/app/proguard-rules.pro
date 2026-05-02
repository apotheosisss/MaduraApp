# Reglas ProGuard — MaduraApp
# Mantener Retrofit + Kotlinx Serialization
-keepattributes Signature
-keepattributes *Annotation*
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response

# Kotlinx Serialization
-keepclassmembers class **$$serializer { *; }
-keepclassmembers class * {
    @kotlinx.serialization.Serializable <methods>;
}
-keep,includedescriptorclasses class cl.duoc.maduraapp.data.dto.** { *; }

# Room — preservar entidades y DAOs
-keep class cl.duoc.maduraapp.data.local.** { *; }
-keep class * extends androidx.room.RoomDatabase
-dontwarn androidx.room.paging.**
